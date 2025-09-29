# csv2playlist.py (multi-file with progress + ETA + logging)
# 功能：
# 1) 自動掃描資料夾內的 playlist_*_final.csv
# 2) 每個 CSV 建立同名的 Spotify 播放清單
# 3) 搜尋並加入曲目，顯示進度與 ETA
# 4) 產生各自的匯入失敗報表 import_report_<清單名>.csv
# 5) 輸出執行過程到 csv2playlist.log 方便追蹤
#
# 需要同資料夾的 token_helper.py 與 tokens.json

import csv
import time
from pathlib import Path
from typing import List, Optional, Tuple

from token_helper import spotify_get, spotify_post

# === 你的設定 ===
USER_ID = "shxdmnb7i6yvw3fvbsjt7mgdf"  # /v1/me 回傳的 id
CSV_DIR = Path(r"C:\Users\USER\Downloads\csv_playlists")  # 放 CSV 的資料夾
CSV_GLOB = "playlist_*_final.csv"  # 要處理的檔名樣式
SEARCH_MARKET = "TW"  # 搜尋市場（market）
LOG_FILE = CSV_DIR / "csv2playlist.log"  # 日誌檔

# ====== 工具函數 ======

def log(msg: str):
    """同時列印到畫面與寫入日誌檔。"""
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def format_eta(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"

def progress_line(done: int, total: int, found: int, not_found: int, start_ts: float) -> str:
    elapsed = time.time() - start_ts
    rate = done / elapsed if elapsed > 0 else 0
    remain = total - done
    eta = remain / rate if rate > 0 else 0
    pct = (done / total * 100) if total > 0 else 0
    return f"{done}/{total} ({pct:.1f}%) | OK {found} / NF {not_found} | elapsed {format_eta(elapsed)} | eta {format_eta(eta)}"

def chunked(lst: List[str], size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

# ====== Spotify 呼叫 ======

def create_playlist(name: str, public: bool, desc: str) -> str:
    resp = spotify_post(
        f"https://api.spotify.com/v1/users/{USER_ID}/playlists",
        json_body={"name": name, "public": public, "description": desc},
    )
    return resp.json()["id"]

def search_track(title: str, artist: str, album: Optional[str], market: str) -> Optional[str]:
    """
    搜尋策略（由嚴到鬆）：
      1) title + artist + album
      2) title + artist
      3) 只用 title
    回傳 spotify:track:... 的 URI 或 None
    """
    def _run(q: str) -> Optional[str]:
        resp = spotify_get(
            "https://api.spotify.com/v1/search",
            params={"q": q, "type": "track", "limit": 1, "market": market},
        )
        items = resp.json().get("tracks", {}).get("items", [])
        return items[0]["uri"] if items else None

    title_q = f'track:"{title}"'
    artist_q = f'artist:"{artist}"' if artist else ""
    album_q = f'album:"{album}"' if album else ""

    if artist and album:
        uri = _run(f"{title_q} {artist_q} {album_q}")
        if uri:
            return uri
    if artist:
        uri = _run(f"{title_q} {artist_q}")
        if uri:
            return uri
    return _run(title_q)

def add_tracks(playlist_id: str, uris: List[str]):
    if not uris:
        return
    for batch in chunked(uris, 100):
        spotify_post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
            json_body={"uris": batch},
        )
        time.sleep(0.2)  # 避免觸發速率限制(rate limit)

# ====== 主要流程 ======

def read_csv_rows(file_path: Path) -> List[dict]:
    with file_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_report(file_path: Path, rows: List[Tuple[str, str, str, str]]):
    # rows: [(Title, Artist, Album, Status), ...]
    with file_path.open("w", encoding="utf-8", newline="") as fo:
        writer = csv.writer(fo)
        writer.writerow(["Title", "Artist", "Album", "Status"])
        writer.writerows(rows)

def process_csv(file_path: Path):
    playlist_name = file_path.stem  # 播放清單名稱直接用檔名
    log(f"=== 開始處理 {file_path.name} → 新建清單: {playlist_name} ===")
    playlist_id = create_playlist(playlist_name, public=False, desc="Imported from CSV")
    log(f"Playlist ID: {playlist_id}")

    rows = read_csv_rows(file_path)
    total = len(rows)
    if total == 0:
        log("此 CSV 無資料，略過")
        return

    start_ts = time.time()
    found_uris: List[str] = []
    not_found_rows: List[Tuple[str, str, str, str]] = []

    try:
        for idx, row in enumerate(rows, start=1):
            title = (row.get("Title") or "").strip()
            artist = (row.get("Artist") or "").strip()
            album = (row.get("Album") or "").strip()

            if not title:
                not_found_rows.append((title, artist, album, "No title"))
            else:
                uri = search_track(title, artist, album or None, market=SEARCH_MARKET)
                if uri:
                    found_uris.append(uri)
                else:
                    not_found_rows.append((title, artist, album, "Not found"))

            # 每 10 首更新一次進度
            if idx % 10 == 0 or idx == total:
                ok = len(found_uris)
                nf = len(not_found_rows)
                log(progress_line(idx, total, ok, nf, start_ts))

    except KeyboardInterrupt:
        log("偵測到中斷，將寫入目前已找到的歌曲並輸出報表...")

    # 寫入播放清單
    log(f"開始加入曲目，共 {len(found_uris)} 首")
    add_tracks(playlist_id, found_uris)
    log("加入曲目完成")

    # 產出報表
    report_file = file_path.with_name(f"import_report_{playlist_name}.csv")
    write_report(report_file, not_found_rows)
    log(f"⚠️ 未匹配歌曲數量: {len(not_found_rows)}，報表：{report_file.resolve()}")
    log(f"=== 完成 {playlist_name}，總耗時 {format_eta(time.time() - start_ts)} ===")

def main():
    LOG_FILE.write_text("", encoding="utf-8")  # 開始前清空日誌
    log(f"掃描資料夾：{CSV_DIR.resolve()}，樣式：{CSV_GLOB}")
    csv_files = sorted(CSV_DIR.glob(CSV_GLOB))
    if not csv_files:
        log("❌ 沒找到任何待處理的 CSV")
        return

    for f in csv_files:
        process_csv(f)

    log("全部清單處理完成")

if __name__ == "__main__":
    main()
