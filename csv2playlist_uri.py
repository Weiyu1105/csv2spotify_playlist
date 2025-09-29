# csv2playlist_uri.py
import csv
import time
from pathlib import Path
from typing import List
from token_helper import spotify_post  # 用你的 token_helper

# === 你的設定 ===
USER_ID = "shxdmnb7i6yvw3fvbsjt7mgdf"
CSV_DIR = Path(r"C:\Users\USER\Downloads\csv_playlists")
CSV_GLOB = "playlist_*_final.csv"
LOG_FILE = CSV_DIR / "csv2playlist_uri.log"

def log(msg: str):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {msg}"
    print(line)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def format_eta(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0: return f"{h}h {m}m {s}s"
    if m > 0: return f"{m}m {s}s"
    return f"{s}s"

def progress_line(done: int, total: int, added: int, start_ts: float) -> str:
    elapsed = time.time() - start_ts
    rate = done / elapsed if elapsed > 0 else 0
    remain = total - done
    eta = remain / rate if rate > 0 else 0
    pct = (done / total * 100) if total > 0 else 0
    return f"{done}/{total} ({pct:.1f}%) | 已加入 {added} | elapsed {format_eta(elapsed)} | eta {format_eta(eta)}"

def create_playlist(name: str, public: bool, desc: str) -> str:
    resp = spotify_post(
        f"https://api.spotify.com/v1/users/{USER_ID}/playlists",
        json_body={"name": name, "public": public, "description": desc},
    )
    return resp.json()["id"]

def add_tracks(playlist_id: str, uris: List[str]):
    total_added = 0
    for i in range(0, len(uris), 100):  # Spotify 限制一次最多 100 首
        batch = uris[i:i+100]
        spotify_post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
            json_body={"uris": batch},
        )
        total_added += len(batch)
        time.sleep(0.2)
    return total_added

def process_csv(file_path: Path):
    playlist_name = file_path.stem
    log(f"=== 開始處理 {file_path.name} → 新建清單: {playlist_name} ===")
    playlist_id = create_playlist(playlist_name, public=False, desc="Imported by TrackURI")
    log(f"Playlist ID: {playlist_id}")

    uris, bad_rows = [], []
    with file_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        total = 0
        for row in reader:
            total += 1
            uri = (row.get("TrackURI") or "").strip()
            if uri.startswith("spotify:track:"):
                uris.append(uri)
            else:
                bad_rows.append([row.get("Title",""), row.get("Artist",""), row.get("Album",""), uri, "Invalid or missing URI"])

    # 開始加入
    log(f"共讀取 {total} 首，其中有效 URI {len(uris)}，無效 {len(bad_rows)}")
    start_ts = time.time()
    added = 0
    for i in range(0, len(uris), 100):
        batch = uris[i:i+100]
        spotify_post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
            json_body={"uris": batch},
        )
        added += len(batch)
        if added % 200 == 0 or added == len(uris):
            log(progress_line(added, len(uris), added, start_ts))
        time.sleep(0.2)

    # 匯出報表（記錄錯誤的）
    if bad_rows:
        report_file = file_path.with_name(f"import_report_{playlist_name}.csv")
        with report_file.open("w", encoding="utf-8", newline="") as fo:
            writer = csv.writer(fo)
            writer.writerow(["Title", "Artist", "Album", "TrackURI", "Status"])
            writer.writerows(bad_rows)
        log(f"⚠️ 有 {len(bad_rows)} 首歌曲的 URI 無效，已寫入 {report_file}")

    log(f"=== 完成 {playlist_name}，成功加入 {added} 首，總耗時 {format_eta(time.time() - start_ts)} ===")

def main():
    LOG_FILE.write_text("", encoding="utf-8")
    csv_files = sorted(CSV_DIR.glob(CSV_GLOB))
    if not csv_files:
        log("❌ 沒找到任何待處理的 CSV")
        return
    for f in csv_files:
        process_csv(f)
    log("全部清單處理完成")

if __name__ == "__main__":
    main()
