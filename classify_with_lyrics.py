# classify_with_lyrics.py
import csv
import re
import requests
from pathlib import Path
from typing import Dict, List

INPUT_FILES = [
    r"C:\Users\USER\Downloads\csv_playlists\csv2spotify_playlist\playlist_中文_final_with_uri_album_v2.csv",
    r"C:\Users\USER\Downloads\csv_playlists\csv2spotify_playlist\playlist_日文_final_with_uri_album_v2.csv",
]
OUTPUT_DIR = Path(r"C:\Users\USER\Downloads\csv_playlists\classified_with_lyrics")
OUTPUT_DIR.mkdir(exist_ok=True)

# 這裡換成你自己的 Genius API Token
GENIUS_API_TOKEN = "OMVzYqdSL80UqmsGvT7KBsia-QQHkEuPLZVpTQCsauN_MZzjVWEzWWz0yXW92QNb"

# === 自訂藝人語言表 ===
ARTIST_LANG_MAP = {
    "周杰倫": "中文",
    "林俊傑": "中文",
    "五月天": "中文",
    "YOASOBI": "日文",
    "米津玄師": "日文",
    "BTS": "韓文",
    "BLACKPINK": "韓文",
    "Taylor Swift": "英文",
    "Adele": "英文",
    "Ed Sheeran": "英文",
}

# === 語言判斷函式 ===
def is_chinese(text): return re.search(r"[\u4e00-\u9fff]", text) is not None
def is_japanese(text): return re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", text) is not None
def is_korean(text): return re.search(r"[\uac00-\ud7af]", text) is not None
def is_english(text): return bool(text) and re.fullmatch(r"[a-zA-Z0-9\s\-\.,!?'()/&:+]+", text) is not None
def is_instrumental(text):
    keywords = ["instrumental", "伴奏", "karaoke", "off vocal", "minus one", "inst"]
    return any(k in text.lower() for k in keywords)

# === 從 Genius API 抓歌詞 ===
def fetch_lyrics(title: str, artist: str) -> str:
    headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
    search_url = "https://api.genius.com/search"
    params = {"q": f"{title} {artist}"}
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        data = response.json()
        hits = data.get("response", {}).get("hits", [])
        if not hits:
            return ""
        song_url = hits[0]["result"]["url"]
        # 簡單取歌詞網頁文字（需要額外套件可用 BeautifulSoup 解析乾淨版）
        page = requests.get(song_url, timeout=10).text
        return page[:3000]  # 避免太長
    except Exception as e:
        print(f"⚠️ 抓歌詞失敗 {title} - {artist}: {e}")
        return ""

# === 分類邏輯 ===
def classify_row(row: Dict[str, str]) -> str:
    artist = row.get("Artist", "").strip()
    title = row.get("Title", "").strip()
    album = row.get("Album", "").strip()

    # Step 1: 藝人
    for key, lang in ARTIST_LANG_MAP.items():
        if key.lower() in artist.lower():
            return lang

    # Step 2: 歌詞
    lyrics = fetch_lyrics(title, artist)
    if lyrics:
        if is_chinese(lyrics): return "中文"
        if is_japanese(lyrics): return "日文"
        if is_korean(lyrics): return "韓文"
        if is_english(lyrics): return "英文"

    # Step 3: fallback → 標題/專輯
    text = f"{title} {album} {artist}"
    if is_instrumental(text): return "伴奏"
    if is_chinese(text): return "中文"
    if is_japanese(text): return "日文"
    if is_korean(text): return "韓文"
    if is_english(text): return "英文"
    return "其他"

# === 主程式 ===
def process_csv(csv_path: Path):
    print(f"\n=== 處理 {csv_path.name} ===")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    categories: Dict[str, List[Dict[str, str]]] = {
        "中文": [], "日文": [], "韓文": [], "英文": [], "伴奏": [], "其他": []
    }

    for row in rows:
        cat = classify_row(row)
        categories[cat].append(row)

    out_dir = OUTPUT_DIR / csv_path.stem
    out_dir.mkdir(exist_ok=True)
    for cat, items in categories.items():
        if not items: continue
        out_file = out_dir / f"{cat}.csv"
        with out_file.open("w", encoding="utf-8-sig", newline="") as fo:
            writer = csv.DictWriter(fo, fieldnames=["Title", "Artist", "Album", "TrackURI"])
            writer.writeheader()
            writer.writerows(items)
        print(f"  - {cat}: {len(items)} 首 → {out_file}")

def main():
    for file in INPUT_FILES:
        process_csv(Path(file))
    print("\n✅ 完成分類，輸出在", OUTPUT_DIR)

if __name__ == "__main__":
    main()
