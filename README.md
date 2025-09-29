

# 🎵 csv2spotify_playlist

## 📖 專案介紹

`csv2spotify_playlist` 是一組 **Spotify 播放清單自動化工具**，透過 Python 腳本與 CSV 檔案互動，讓你可以：

* 將 **本地 CSV 清單匯入 Spotify**，自動建立播放清單並批次加入歌曲
* 從 **Spotify 播放清單下載歌曲清單**，輸出成 CSV
* 進一步利用 YAML 與歌詞分析做 **語言分類** 與 **歌單合併整理**

專案同時支援 **命令列介面（CLI）** 與 **圖形介面（GUI, Tkinter）**。

---

## ✨ 功能特色

* ✅ **CSV → Spotify**：直接用 `TrackURI` 批次匯入，準確快速
* ✅ **Spotify → CSV**：可下載單一或全部清單
* ✅ **多清單批次匯入**：一次匯入多個 CSV，並自訂清單名稱前後綴
* ✅ **GUI 操作**：不熟 CLI 也可用 `csv2playlist_gui.py` 視覺化選檔匯入
* ✅ **語言分類**：利用 `artist_lang_map.yaml` + 歌詞輔助分類，將歌曲整理成不同語言清單
* ✅ **Token 管理自動化**：支援 PKCE 登入、自動刷新 access_token

---

## ⚙️ 安裝與需求

### 1. 環境需求

* Python 3.9+
* Spotify 開發者帳號與 Client 設定（PKCE 流程）

### 2. 安裝依賴

```bash
pip install requests pyyaml
```

---

## 🚀 使用方式

### 1. 取得 Spotify Token

```bash
python spotify_pkce_local.py
```

登入後會在專案目錄產生 `tokens.json`。

若 access_token 過期，可用：

```bash
python refresh_token.py
```

---

### 2. 匯入 CSV → Spotify

**推薦：用 TrackURI 版本**

```bash
python csv2playlist_uri.py
```

**GUI 版**

```bash
python csv2playlist_gui.py
```

選擇一個或多個 `playlist_*_with_uri_album_v2.csv` 檔案，自動建立播放清單並顯示進度。

---

### 3. Spotify → CSV

```bash
python download_playlists.py
```

* 可輸入清單編號或 `all`
* 輸出格式：`Title,Artist,Album,TrackURI`

---

### 4. 匯入多個清單

```bash
python spotify_import_multi_playlists_clean.py playlist_中文_final.csv playlist_日文_final.csv
```

或使用完整版：

```bash
python spotify_import_multi_playlists.py --public --playlist-prefix "Lang | " --playlist-suffix " (2025)" playlist_*.csv
```

---

### 5. 歌單分類 / 合併

```bash
python classify_pick_and_merge.py
```

自動比對 `artist_lang_map.yaml`，並將歌曲歸類到「中文、日文、韓文、英文、西班牙語、伴奏、其他」。

---

## 📂 專案結構

```text
csv2spotify_playlist/
├─ playlist_*.csv / *_with_uri_album_v2.csv   # 各語言歌單
├─ csv2playlist_uri.py                        # 用 URI 匯入 (推薦)
├─ csv2playlist_gui.py                        # GUI 版匯入工具
├─ download_playlists.py                      # 下載 Spotify → CSV
├─ spotify_import_multi_playlists.py          # 多清單匯入 (完整版)
├─ spotify_import_multi_playlists_clean.py    # 多清單匯入 (簡易版)
├─ spotify_pkce_local.py                      # PKCE 登入
├─ refresh_token.py                           # 手動刷新 token
├─ token_helper.py                            # Token 管理模組
├─ classify_pick_and_merge.py                 # 語言分類 / 合併工具
├─ classify_with_lyrics.py                    # 歌詞輔助分類
├─ artist_lang_map.yaml                       # 藝人語言對照表
├─ tokens.json                                # 儲存 access_token / refresh_token
└─ README.md / FILES.md                       # 專案文件
```

---

## ❓ 常見問題

**Q1. 為什麼有些歌曲沒有成功匯入？**

* 請確認 CSV 裡是否有正確的 `TrackURI`
* 若使用舊版 `csv2playlist.py`，搜尋結果可能不完整，建議改用 `csv2playlist_uri.py`

**Q2. Spotify 限制一次最多加 100 首，怎麼解決？**

* 腳本已經內建分批與延遲機制，每批 100 首並 sleep 0.2 秒

**Q3. token 失效怎麼辦？**

* 可重新執行 `spotify_pkce_local.py` 取得新的 token
* 或執行 `refresh_token.py` 更新

---

## 📜 授權

MIT License

---

要不要我直接幫你把這份 **全新 README.md** 存成檔案，讓你可以直接下載？
