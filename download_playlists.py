# download_playlists.py
# 作用：列出使用者的所有播放清單，讓使用者選擇要下載哪幾個，然後把每個清單的曲目存成 CSV 檔案
# 需要先用 spotify_pkce_local.py 取得 tokens.json
# 需要 token_helper.py 裡的 ensure_access_token 函式
# 會把 CSV 檔案存到目前目錄
# CSV 格式：Title,Artist,Album,TrackURI
# 參考 spotify_pkce_local.py 與 token_helper.py
# pip install requests
# python download_playlists.py
import requests
import csv
import time
from token_helper import ensure_access_token   # ✅ 改這裡

USER_ID = "shxdmnb7i6yvw3fvbsjt7mgdf"

def get_my_playlists(limit=50):
    """列出目前使用者的所有播放清單"""
    playlists = []
    offset = 0
    while True:
        token = ensure_access_token()   # ✅ 改這裡
        resp = requests.get(
            f"https://api.spotify.com/v1/me/playlists?limit={limit}&offset={offset}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = resp.json()
        if "items" not in data:
            print("❌ 取得播放清單失敗:", data)
            break
        playlists.extend(data["items"])
        if data.get("next") is None:
            break
        offset += limit
    return playlists

def get_playlist_tracks(playlist_id):
    """抓取單一播放清單的所有歌曲"""
    tracks = []
    limit = 100
    offset = 0
    while True:
        token = ensure_access_token()   # ✅ 改這裡
        resp = requests.get(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit={limit}&offset={offset}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = resp.json()
        if "items" not in data:
            print("❌ 取得歌單曲目失敗:", data)
            break
        for item in data["items"]:
            track = item.get("track")
            if not track:
                continue
            tracks.append({
                "Title": track.get("name", ""),
                "Artist": ", ".join([a["name"] for a in track.get("artists", [])]),
                "Album": track.get("album", {}).get("name", ""),
                "TrackURI": track.get("uri", ""),
            })
        if data.get("next") is None:
            break
        offset += limit
    return tracks

def save_to_csv(tracks, filename):
    """把歌曲列表寫到 CSV"""
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Artist", "Album", "TrackURI"])
        writer.writeheader()
        writer.writerows(tracks)
    print(f"✅ 已輸出 {len(tracks)} 首歌到 {filename}")

def main():
    playlists = get_my_playlists()
    if not playlists:
        print("❌ 沒有找到任何播放清單")
        return

    print("\n=== 你的 Spotify 播放清單 ===")
    for idx, pl in enumerate(playlists, 1):
        print(f"{idx}. {pl['name']} (Tracks: {pl['tracks']['total']})")

    choice = input("\n輸入要下載的清單編號（可輸入多個，用逗號分隔，或輸入 all 全部下載）：")

    if choice.strip().lower() == "all":
        indexes = range(1, len(playlists) + 1)
    else:
        indexes = [int(x.strip()) for x in choice.split(",") if x.strip().isdigit()]

    for idx in indexes:
        if 1 <= idx <= len(playlists):
            pl = playlists[idx - 1]
            print(f"\n🎵 正在下載: {pl['name']} ...")
            tracks = get_playlist_tracks(pl["id"])
            safe_name = pl['name'].replace(" ", "_").replace("/", "_")
            filename = f"{safe_name}.csv"
            save_to_csv(tracks, filename)
            time.sleep(0.2)
        else:
            print(f"⚠️ 無效的編號: {idx}")

if __name__ == "__main__":
    main()
