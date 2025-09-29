# csv2spotify_playlist

# 🎵 Spotify Playlist 工具集

這個資料夾包含一系列 Python 腳本與 CSV 檔案，用來實現 Spotify 播放清單的 **匯入** 與 **下載**。  
流程主要分成兩個方向：

1. **匯入 CSV → Spotify**  
   - 把本地的歌曲清單（含 Track URI）匯入到 Spotify 播放清單。
2. **下載 Spotify → CSV**  
   - 從 Spotify 抓取播放清單，輸出成 CSV 檔案。

---

## 📂 資料夾內容

### 📑 CSV 清單
這些是準備匯入的播放清單，含有 `Title, Artist, Album, TrackURI` 欄位：
- `playlist_中文_final.csv`
- `playlist_日文_final.csv`
- `playlist_韓文_final.csv`
- `playlist_英文_final.csv`
- `playlist_伴奏_final.csv`
- `playlist_其他_final.csv`

進階版本（帶 `_with_uri_album_v2` 後綴）：  
- `playlist_中文_final_with_uri_album_v2.csv`
- `playlist_日文_final_with_uri_album_v2.csv`
- `playlist_韓文_final_with_uri_album_v2.csv`
- `playlist_英文_final_with_uri_album_v2.csv`
- `playlist_伴奏_final_with_uri_album_v2.csv`
- `playlist_其他_final_with_uri_album_v2.csv`

> 📌 這些檔案主要差異是 URI 與專輯資訊是否完整。

---

### 🐍 Python 腳本

| 檔名 | 功能 |
|------|------|
| `spotify_pkce_local.py` | 啟動 **PKCE 授權流程**，登入 Spotify 並取得 token，會儲存到 `tokens.json` |
| `refresh_token.py` | 使用 `refresh_token` 更新 `access_token` |
| `token_helper.py` | 提供 `ensure_access_token()` 等工具函式，統一存取/更新 token |
| `csv2playlist.py` | 舊版：以「Title + Artist」搜尋歌曲，匯入播放清單（速度較慢） |
| `csv2playlist_uri.py` | **新版：直接用 Track URI 批次加入歌曲**，速度快、準確 |
| `spotify_import_multi_playlists.py` | 匯入多個播放清單的腳本（含 Title/Artist 搜尋） |
| `spotify_import_multi_playlists_clean.py` | 上一個腳本的精簡整理版 |
| `download_playlists.py` | 從 Spotify **下載歌單 → CSV**，支援多選或一鍵下載全部 |

---

### ⚙️ Token 與設定檔
- `tokens.json`  
  儲存目前的 `access_token` 與 `refresh_token`。  
  所有腳本都會共用這個檔案。

---

### 📝 日誌與報表
- `csv2playlist_uri.log`  
  執行 `csv2playlist_uri.py` 時的過程紀錄（進度、耗時）。  

- `import_report_playlist_日文_final_with_uri_album_v2.csv`  
  匯入報表，紀錄哪些歌曲 URI 缺失或錯誤。

---

### 🔧 其他
- `.git` / `__pycache__` → Git 版本控制與 Python 編譯暫存檔，無需手動操作。

---

## 🚀 使用方式

### 1. 匯入 CSV → Spotify
```powershell
cd C:\Users\USER\Downloads\csv_playlists\csv2spotify_playlist
python csv2playlist_uri.py
