# -*- coding: utf-8 -*-
"""
GUI 版 Spotify CSV 匯入工具
- 用 Tkinter 實作視覺化介面 (GUI)
- 可多選 CSV
- 顯示進度條與即時日誌
- 與原本 csv2playlist_uri.py 的核心邏輯相容
"""

import csv
import time
import threading
from pathlib import Path
from typing import List, Tuple
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from token_helper import spotify_post  # 沿用你的 token_helper

# === 你的設定 ===
USER_ID = "shxdmnb7i6yvw3fvbsjt7mgdf"

# Spotify 一次最多加入 100 首
BATCH_SIZE = 100

# 速率限制保守延遲
SLEEP_AFTER_BATCH_SEC = 0.2


# -----------------------------
# 共用工具
# -----------------------------
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


def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def log_append(widget: tk.Text, msg: str) -> None:
    widget.configure(state="normal")
    widget.insert("end", f"[{now_ts()}] {msg}\n")
    widget.see("end")
    widget.configure(state="disabled")


# -----------------------------
# Spotify API 包裝
# -----------------------------
def create_playlist(user_id: str, name: str, public: bool, desc: str) -> str:
    resp = spotify_post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        json_body={"name": name, "public": public, "description": desc},
    )
    data = resp.json()
    return data["id"]


def add_tracks(playlist_id: str, uris: List[str], log_cb, progress_cb) -> int:
    total_added = 0
    start_ts = time.time()
    for i in range(0, len(uris), BATCH_SIZE):
        batch = uris[i:i + BATCH_SIZE]
        spotify_post(
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
            json_body={"uris": batch},
        )
        total_added += len(batch)
        elapsed = time.time() - start_ts
        rate = total_added / elapsed if elapsed > 0 else 0.0
        remain = len(uris) - total_added
        eta = remain / rate if rate > 0 else 0.0
        # UI 更新
        progress_cb(total_added, len(uris))
        log_cb(f"已加入 {total_added}/{len(uris)} | elapsed {format_eta(elapsed)} | eta {format_eta(eta)}")
        time.sleep(SLEEP_AFTER_BATCH_SEC)
    return total_added


# -----------------------------
# CSV 處理
# -----------------------------
def read_csv_collect_uris(file_path: Path) -> Tuple[List[str], List[List[str]], int]:
    """回傳 (有效URIs, 問題列清單, 總筆數)"""
    uris, bad_rows = [], []
    total = 0
    with file_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            uri = (row.get("TrackURI") or "").strip()
            if uri.startswith("spotify:track:"):
                uris.append(uri)
            else:
                bad_rows.append([
                    row.get("Title", ""),
                    row.get("Artist", ""),
                    row.get("Album", ""),
                    uri,
                    "Invalid or missing URI"
                ])
    return uris, bad_rows, total


def write_bad_report(file_path: Path, playlist_name: str, bad_rows: List[List[str]]) -> Path:
    report_file = file_path.with_name(f"import_report_{playlist_name}.csv")
    with report_file.open("w", encoding="utf-8", newline="") as fo:
        writer = csv.writer(fo)
        writer.writerow(["Title", "Artist", "Album", "TrackURI", "Status"])
        writer.writerows(bad_rows)
    return report_file


def process_one_csv(file_path: Path, user_id: str, log_cb, progress_cb) -> None:
    playlist_name = file_path.stem
    log_cb(f"=== 開始處理 {file_path.name} → 新建清單: {playlist_name} ===")

    # 新建播放清單
    playlist_id = create_playlist(user_id, playlist_name, public=False, desc="Imported by TrackURI")
    log_cb(f"Playlist ID: {playlist_id}")

    uris, bad_rows, total = read_csv_collect_uris(file_path)
    log_cb(f"共讀取 {total} 首，其中有效 URI {len(uris)}，無效 {len(bad_rows)}")

    # 進度初始化
    progress_cb(0, max(1, len(uris)))

    # 加入曲目
    added = 0
    if uris:
        added = add_tracks(playlist_id, uris, log_cb, progress_cb)

    # 問題報表
    if bad_rows:
        report_file = write_bad_report(file_path, playlist_name, bad_rows)
        log_cb(f"⚠️ 有 {len(bad_rows)} 首歌曲的 URI 無效，已寫入 {report_file}")

    log_cb(f"=== 完成 {playlist_name}，成功加入 {added} 首 ===")


# -----------------------------
# GUI 主程式
# -----------------------------
class CSV2PlaylistGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Spotify CSV 匯入工具（GUI）")

        # 上層框架：控制列
        frm_top = ttk.Frame(root)
        frm_top.pack(fill="x", padx=10, pady=10)

        self.btn_choose = ttk.Button(frm_top, text="選擇 CSV 檔案", command=self.choose_files)
        self.btn_choose.pack(side="left")

        self.btn_clear = ttk.Button(frm_top, text="清除清單", command=self.clear_list)
        self.btn_clear.pack(side="left", padx=6)

        self.btn_start = ttk.Button(frm_top, text="開始匯入", command=self.start_import)
        self.btn_start.pack(side="right")

        # 中間：檔案清單
        frm_mid = ttk.LabelFrame(root, text="待匯入清單")
        frm_mid.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self.list_files = tk.Listbox(frm_mid, height=8, selectmode="extended")
        self.list_files.pack(fill="both", expand=True, padx=8, pady=8)

        # 進度條
        frm_prog = ttk.Frame(root)
        frm_prog.pack(fill="x", padx=10, pady=(0,10))

        self.progress = ttk.Progressbar(frm_prog, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", expand=True)

        # 日誌
        frm_log = ttk.LabelFrame(root, text="日誌 Log")
        frm_log.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self.txt_log = tk.Text(frm_log, height=12, state="disabled")
        self.txt_log.pack(fill="both", expand=True, padx=8, pady=8)

        # 狀態
        self.status_var = tk.StringVar(value="就緒")
        self.lbl_status = ttk.Label(root, textvariable=self.status_var, anchor="w")
        self.lbl_status.pack(fill="x", padx=10, pady=(0,10))

        self.selected_files: List[Path] = []
        self._worker: threading.Thread | None = None
        self._stop_flag = False

    # --- 事件處理 ---
    def choose_files(self):
        filenames = filedialog.askopenfilenames(
            title="選擇 CSV 檔案",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not filenames:
            return
        self.selected_files = [Path(f) for f in filenames]
        self.list_files.delete(0, "end")
        for p in self.selected_files:
            self.list_files.insert("end", str(p))
        self.set_status(f"已選擇 {len(self.selected_files)} 個檔案")

    def clear_list(self):
        self.selected_files = []
        self.list_files.delete(0, "end")
        self.progress.configure(value=0, maximum=100)
        self.set_status("清單已清空")

    def start_import(self):
        if self._worker and self._worker.is_alive():
            messagebox.showinfo("提示", "匯入中，請稍候")
            return
        if not self.selected_files:
            messagebox.showwarning("提示", "請先選擇至少一個 CSV")
            return

        self._stop_flag = False
        self.progress.configure(value=0, maximum=100)
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")
        self.set_status("開始匯入")

        # 背景執行，避免 GUI 卡住
        self._worker = threading.Thread(target=self._run_import, daemon=True)
        self._worker.start()

    # --- 背景主流程 ---
    def _run_import(self):
        try:
            total_files = len(self.selected_files)
            file_idx = 0
            for file_path in self.selected_files:
                file_idx += 1
                self.log(f"({file_idx}/{total_files}) 準備處理：{file_path.name}")
                # 單檔進度重置
                self.update_progress(0, 1)
                process_one_csv(
                    file_path=file_path,
                    user_id=USER_ID,
                    log_cb=self.log,
                    progress_cb=self.update_progress
                )
            self.set_status("全部清單處理完成")
            self.log("全部清單處理完成")
        except Exception as e:
            self.set_status("發生錯誤，請查看日誌")
            self.log(f"❌ 發生例外：{e}")

    # --- UI 更新器 ---
    def log(self, msg: str):
        self.root.after(0, log_append, self.txt_log, msg)

    def set_status(self, text: str):
        def _set():
            self.status_var.set(text)
        self.root.after(0, _set)

    def update_progress(self, done: int, total: int):
        total = max(1, total)
        pct = int(done / total * 100)
        pct = max(0, min(100, pct))
        def _set():
            self.progress.configure(maximum=100, value=pct)
        self.root.after(0, _set)


def main():
    root = tk.Tk()
    app = CSV2PlaylistGUI(root)
    root.geometry("820x680")
    root.mainloop()


if __name__ == "__main__":
    main()
