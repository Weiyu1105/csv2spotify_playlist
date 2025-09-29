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

---

# 📂 csv2spotify_playlist 專案結構

```text
csv2spotify_playlist/
├─ playlist_中文_final.csv
├─ playlist_中文_final_with_uri_album_v2.csv
├─ playlist_日文_final.csv
├─ playlist_日文_final_with_uri_album_v2.csv
├─ playlist_韓文_final.csv
├─ playlist_韓文_final_with_uri_album_v2.csv
├─ playlist_英文_final.csv
├─ playlist_英文_final_with_uri_album_v2.csv
├─ playlist_伴奏_final.csv
├─ playlist_伴奏_final_with_uri_album_v2.csv
├─ playlist_其他_final.csv
├─ playlist_其他_final_with_uri_album_v2.csv
│
├─ artist_lang_map.yaml                  # 藝人語言對照表
├─ check_yaml.py                         # 驗證 YAML 對照檔
├─ classify_pick_and_merge.py            # 歌單分類與合併
├─ classify_with_lyrics.py               # 歌詞輔助分類
│
├─ csv2playlist.py                       # 舊版 CSV 匯入 (Title+Artist 搜尋)
├─ csv2playlist_uri.py                   # 新版 CSV 匯入 (Track URI)
├─ csv2playlist_gui.py                   # GUI 版匯入工具 (Tkinter)
├─ download_playlists.py                 # Spotify → CSV 下載
│
├─ spotify_pkce_local.py                 # 啟動 PKCE 授權流程
├─ refresh_token.py                      # 更新 token
├─ token_helper.py                       # Token 管理輔助
├─ tokens.json                           # 儲存存取憑證
│
├─ spotify_import_multi_playlists.py     # 匯入多個清單
├─ spotify_import_multi_playlists_clean.py
│
├─ README.md                             # 專案說明文件
├─ csv2playlist_uri.log                  # 執行日誌
├─ import_report_playlist_日文_final_with_uri_album_v2.csv  # 匯入報表
├─ lyrics_cache.json                     # 歌詞快取
│
├─ .git/                                 # Git 版本控制
├─ __pycache__/                          # Python 編譯暫存
└─ test/                                 # 測試資料夾
```

---

## 📑 說明

- **CSV 歌單**：各語言／用途的播放清單（含 `_with_uri_album_v2` 版，帶完整 URI 與專輯資訊）  
- **Python 腳本**：  
  - `csv2playlist*.py` 系列：負責播放清單匯入  
  - `download_playlists.py`：下載 Spotify 播放清單  
  - `classify_*.py`：分類與整理工具  
- **Token 管理**：`spotify_pkce_local.py`, `refresh_token.py`, `token_helper.py`, `tokens.json`  
- **日誌 / 報表**：匯入過程紀錄與錯誤報表  
- **其他**：`artist_lang_map.yaml` 提供語言分類對照表；`lyrics_cache.json` 儲存歌詞快取