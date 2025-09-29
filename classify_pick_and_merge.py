# classify_pick_and_merge.py
# 功能：
# 1) 用圖形介面挑選多個 CSV（檔名不限，任選幾個）
# 2) 合併後分類成 7 份：中文 / 日文 / 韓文 / 英文 / 西班牙語 / 伴奏 / 其他
# 3) 可填入 Genius Access Token（環境變數 GENIUS_API_TOKEN）以歌詞(lyrics)輔助判斷；未填則略過歌詞判斷
# 4) 僅從 artist_lang_map.yaml 讀取「藝人→語言」對照（沒有就空表）

import csv
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import Counter

import requests
from bs4 import BeautifulSoup

# ====== 可調參數 ======
GENIUS_API_TOKEN_FALLBACK = ""   # 留空：優先走環境變數
MAX_LYRICS_CHARS = 20000
REQUEST_TIMEOUT = 12
SLEEP_BETWEEN_REQ = 0.3  # 速度 vs 穩定性

# YAML 檔案路徑（藝人→語言清單）
ARTIST_YAML_PATH = Path("artist_lang_map.yaml")

# ====== 語系偵測（Language Detection）=====
def is_chinese(t: str) -> bool:
    return re.search(r"[\u4e00-\u9fff]", t) is not None

def is_japanese(t: str) -> bool:
    return re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", t) is not None

def is_korean(t: str) -> bool:
    return re.search(r"[\uac00-\ud7af]", t) is not None

def is_spanish(t: str) -> bool:
    # 常見西班牙語元音與 ñ, ¡, ¿ 等符號
    return re.search(r"[ñáéíóúü¡¿]", t, re.IGNORECASE) is not None

def is_english(t: str) -> bool:
    if not t:
        return False
    if is_chinese(t) or is_japanese(t) or is_korean(t) or is_spanish(t):
        return False
    letters = re.findall(r"[A-Za-z]", t)
    return len(letters) >= 3

def is_instrumental(t: str) -> bool:
    kw = [
        "instrumental", "伴奏", "karaoke", "off vocal", "minus one", "inst",
        "バックトラック", "노래방", "mr "
    ]
    tl = t.lower()
    return any(k in tl for k in kw)

# ====== 快取（lyrics_cache.json）=====
CACHE_PATH = Path("lyrics_cache.json")

def load_cache() -> Dict[str, str]:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_cache(cache: Dict[str, str]) -> None:
    try:
        CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def cache_key(title: str, artist: str) -> str:
    return json.dumps([title.strip(), artist.strip()], ensure_ascii=False)

# ====== 讀 YAML（artist_lang_map.yaml）======
def load_artist_map_from_yaml(yaml_path: Path) -> Dict[str, str]:
    if not yaml_path.exists():
        print(f"ℹ️ 找不到 YAML：{yaml_path}，將只用歌詞/字元偵測作為後援分類。")
        return {}
    try:
        import yaml
    except ImportError:
        print("⚠️ 未安裝 pyyaml，跳過載入 YAML（執行：pip install pyyaml）")
        return {}
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        artist_map: Dict[str, str] = {}
        if isinstance(data, dict):
            for lang, artists in data.items():
                if isinstance(artists, list):
                    for name in artists:
                        if isinstance(name, str) and name.strip():
                            artist_map[name.strip()] = lang
        print(f"✅ 已載入 YAML：{yaml_path}，共 {len(artist_map)} 筆對照")
        return artist_map
    except Exception as e:
        print(f"⚠️ YAML 載入失敗：{e}\nℹ️ 將只用歌詞/字元偵測作為後援分類。")
        return {}

def build_artist_lang_map() -> Dict[str, str]:
    return load_artist_map_from_yaml(ARTIST_YAML_PATH)

# ====== Genius 歌詞（Lyrics）======
def get_genius_token() -> str:
    return os.environ.get("GENIUS_API_TOKEN") or GENIUS_API_TOKEN_FALLBACK or ""

def fetch_lyrics(title: str, artist: str, cache: Dict[str, str]) -> str:
    token = get_genius_token()
    if not token:
        return ""
    key = cache_key(title, artist)
    if key in cache:
        return cache[key]

    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(
            "https://api.genius.com/search",
            headers=headers,
            params={"q": f"{title} {artist}"},
            timeout=REQUEST_TIMEOUT,
        )
        hits = r.json().get("response", {}).get("hits", [])
        if not hits:
            cache[key] = ""
            return ""

        song_url = hits[0]["result"]["url"]
        html = requests.get(song_url, timeout=REQUEST_TIMEOUT).text
        soup = BeautifulSoup(html, "lxml")

        parts = []
        for div in soup.select('div[data-lyrics-container="true"]'):
            parts.append(div.get_text(separator="\n"))
        if not parts:
            for div in soup.select("div.Lyrics__Container-sc-1ynbvzw-1"):
                parts.append(div.get_text(separator="\n"))
        if not parts:
            for p in soup.select("div.lyrics p"):
                parts.append(p.get_text(separator="\n"))

        lyrics = "\n".join(parts).strip()
        lyrics = re.sub(r"\n{3,}", "\n\n", lyrics)[:MAX_LYRICS_CHARS]

        cache[key] = lyrics
        time.sleep(SLEEP_BETWEEN_REQ)
        return lyrics
    except Exception:
        cache[key] = ""
        return ""

# ====== 讀寫 CSV ======
REQ_COLS = ["Title", "Artist", "Album", "TrackURI"]

def normalize_headers(headers: List[str]) -> Dict[str, str]:
    lm = {h.lower(): h for h in headers or []}
    mapping = {}
    for c in REQ_COLS:
        if c.lower() not in lm:
            raise ValueError(f"找不到必要欄位：{c}（實際欄位：{headers}）")
        mapping[c] = lm[c.lower()]
    return mapping

def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        mapping = normalize_headers(reader.fieldnames)
        rows = []
        for r in reader:
            rows.append({
                "Title": r.get(mapping["Title"], "").strip(),
                "Artist": r.get(mapping["Artist"], "").strip(),
                "Album": r.get(mapping["Album"], "").strip(),
                "TrackURI": r.get(mapping["TrackURI"], "").strip(),
            })
        return rows

def _next_available_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    i = 1
    while True:
        candidate = path.with_name(f"{stem} ({i}){suffix}")
        if not candidate.exists():
            return candidate
        i += 1

def write_rows(path: Path, rows: List[Dict[str, str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=REQ_COLS)
            w.writeheader()
            w.writerows(rows)
    except PermissionError:
        alt = _next_available_path(path)
        print(f"⚠️ 檔案被佔用或不可覆寫：{path.name} → 另存為 {alt.name}")
        with alt.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=REQ_COLS)
            w.writeheader()
            w.writerows(rows)

# ====== 多藝人（Multi-Artist）處理 ======
SEP_PATTERN = re.compile(
    r"\s*;\s*|\s*,\s*|\s*/\s*|\s*&\s*|\s+\+\s+|\s+x\s+|\s+X\s+|\s+feat\.?\s+|\s+with\s+",
    flags=re.IGNORECASE
)

def split_artists(artist_field: str) -> List[str]:
    if not artist_field:
        return []
    parts = SEP_PATTERN.split(artist_field)
    return [p.strip() for p in parts if p.strip()]

def vote_lang_by_yaml(artists: List[str], artist_map: Dict[str, str]) -> Optional[str]:
    votes: List[str] = []
    for a in artists:
        for key, lang in artist_map.items():
            if key.lower() in a.lower():
                votes.append(lang)
                break
    if not votes:
        return None
    uniq = set(votes)
    if len(uniq) == 1:
        return votes[0]
    c = Counter(votes)
    lang, cnt = c.most_common(1)[0]
    if cnt >= 2 and cnt > (len(votes) - cnt):
        return lang
    return None

# ====== 單首分類（Classification）======
def classify_row(row: Dict[str, str], cache: Dict[str, str],
                 artist_map: Dict[str, str], unknown_artists: Set[str]) -> str:
    artist = row.get("Artist", "") or ""
    title  = row.get("Title", "")  or ""
    album  = row.get("Album", "")  or ""

    # 0) 多藝人 → YAML 判斷
    artists_list = split_artists(artist)
    if len(artists_list) >= 2:
        yaml_lang = vote_lang_by_yaml(artists_list, artist_map)
        if yaml_lang:
            return yaml_lang

    # 1) YAML 單藝人
    matched = False
    for key, lang in artist_map.items():
        if key.lower() in artist.lower():
            matched = True
            return lang
    if not matched and artist.strip():
        unknown_artists.add(artist.strip())

    # 2) 歌詞判斷
    lyrics = fetch_lyrics(title, artist, cache)
    if lyrics:
        if is_instrumental(lyrics): return "伴奏"
        if is_chinese(lyrics):      return "中文"
        if is_japanese(lyrics):     return "日文"
        if is_korean(lyrics):       return "韓文"
        if is_spanish(lyrics):      return "西班牙語"
        if is_english(lyrics):      return "英文"

    # 3) fallback
    text = f"{title} {album} {artist}"
    if is_instrumental(text): return "伴奏"
    if is_chinese(text):      return "中文"
    if is_japanese(text):     return "日文"
    if is_korean(text):       return "韓文"
    if is_spanish(text):      return "西班牙語"
    if is_english(text):      return "英文"
    return "其他"

# ====== 檔案選擇（GUI）======
def pick_files_gui() -> List[Path]:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("選擇 CSV", "請選擇要分類的 1~N 個 CSV（可多選）")
    paths = filedialog.askopenfilenames(
        title="選擇要分類的 CSV（可多選）",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    return [Path(p) for p in paths]

def pick_outdir_gui(default: Path) -> Path:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    outdir = filedialog.askdirectory(title="選擇輸出資料夾", initialdir=str(default))
    return Path(outdir) if outdir else default

# ====== 主流程 ======
def main():
    csv_paths = pick_files_gui()
    if not csv_paths:
        print("❌ 未選擇任何 CSV，結束。")
        return

    artist_map = build_artist_lang_map()

    all_rows: List[Dict[str, str]] = []
    for p in csv_paths:
        all_rows.extend(read_rows(p))
    print(f"總筆數：{len(all_rows)}")

    default_out = Path.cwd() / "classified_pick"
    out_root = pick_outdir_gui(default_out)
    out_root.mkdir(parents=True, exist_ok=True)

    buckets: Dict[str, List[Dict[str, str]]] = {
        "中文": [], "日文": [], "韓文": [], "英文": [], "西班牙語": [], "伴奏": [], "其他": []
    }

    cache = load_cache()
    unknown_artists: Set[str] = set()

    for i, r in enumerate(all_rows, start=1):
        cat = classify_row(r, cache, artist_map, unknown_artists)
        buckets[cat].append(r)
        if i % 50 == 0 or i == len(all_rows):
            print(f"進度：{i}/{len(all_rows)}")

    total_info = []
    for cat, items in buckets.items():
        if not items:
            continue
        out_csv = out_root / f"playlist_{cat}.csv"
        write_rows(out_csv, items)
        total_info.append((cat, len(items), out_csv.name))
        print(f"→ {cat}: {len(items)} 首 → {out_csv.name}")

    if unknown_artists:
        unknown_path = out_root / "unknown_artists.txt"
        unknown_path.write_text("\n".join(sorted(unknown_artists)), encoding="utf-8")
        print(f"📝 已輸出未知藝人名單：{unknown_path}")

    save_cache(cache)

    if total_info:
        print("—— 統計 ——")
        for cat, cnt, name in total_info:
            print(f"• {cat}: {cnt} 首 → {name}")
    print("✅ 完成！")

if __name__ == "__main__":
    main()
