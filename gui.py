import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from project import download_file, download_youtube


class DownloaderGUI(tk.Tk):
    """Simple GUI wrapper for the downloader project."""

    def __init__(self) -> None:
        super().__init__()
        self.title("File & YouTube Downloader")
        self.geometry("500x300")
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.youtube_var = tk.BooleanVar()
        self.no_resume_var = tk.BooleanVar()
        self.quality_var = tk.StringVar()
        self.pause_event = threading.Event()
        self.cancel_event = threading.Event()
        self._is_downloading = False
        self._progress_stats = None

        self.url_var.trace_add("write", lambda *args: self._on_url_change())

        self._create_widgets()

    def _on_url_change(self):
        # If YouTube mode is on and URL changes, repopulate qualities
        if self.youtube_var.get():
            self._populate_youtube_qualities()

    def _create_widgets(self) -> None:
        ttk.Label(self, text="URL:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.url_var, width=50).grid(
            row=0, column=1, columnspan=3, pady=5
        )

        ttk.Label(self, text="Output File:").grid(row=1, column=0, sticky="e", padx=5)
        ttk.Entry(self, textvariable=self.output_var, width=40).grid(row=1, column=1, pady=5)
        ttk.Button(self, text="Browse", command=self._browse_file).grid(
            row=1, column=2, padx=5, pady=5
        )

        ttk.Checkbutton(self, text="YouTube Mode", variable=self.youtube_var, command=self._toggle_youtube_options).grid(
            row=2, column=1, sticky="w"
        )
        ttk.Checkbutton(self, text="Disable Resume", variable=self.no_resume_var).grid(
            row=2, column=2, sticky="w"
        )

        ttk.Label(self, text="Quality:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        quality_options = ["best", "worst", "144p", "240p", "360p", "480p", "720p", "1080p"]
        self.quality_var.set("best")
        self.quality_combo = ttk.Combobox(self, textvariable=self.quality_var, values=quality_options, state="readonly", width=10)
        self.quality_combo.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.quality_label = ttk.Label(self, text="Quality:")
        self.quality_label.grid(row=3, column=0, sticky="e", padx=5, pady=5)

        self.progress = ttk.Progressbar(self, length=400, mode="determinate")
        self.progress.grid(row=4, column=0, columnspan=4, padx=5, pady=10)
        self.status_label = ttk.Label(self, text="")
        self.status_label.grid(row=5, column=0, columnspan=4)

        self.download_btn = ttk.Button(self, text="Download", command=self._start_download)
        self.download_btn.grid(row=6, column=3, sticky="e", padx=5, pady=10)

        self.pause_btn = ttk.Button(self, text="Pause", command=self._toggle_pause, state=tk.DISABLED)
        self.pause_btn.grid(row=6, column=2, sticky="e", padx=5, pady=10)

        self.cancel_btn = ttk.Button(self, text="Cancel", command=self._cancel_download, state=tk.DISABLED)
        self.cancel_btn.grid(row=6, column=1, sticky="e", padx=5, pady=10)

        self.youtube_var.trace_add("write", lambda *args: self._toggle_youtube_options())

    def _browse_file(self) -> None:
        path = filedialog.asksaveasfilename()
        if path:
            self.output_var.set(path)

    def _toggle_youtube_options(self):
        if self.youtube_var.get():
            self.quality_label.grid()
            self.quality_combo.grid()
            self._populate_youtube_qualities()
        else:
            self.quality_label.grid_remove()
            self.quality_combo.grid_remove()

    def _populate_youtube_qualities(self):
        url = self.url_var.get().strip()
        self.quality_combo['values'] = ['Updating...']
        self.quality_var.set('Updating...')
        self.quality_combo.update_idletasks()
        self.status_label.config(text="Fetching available video qualities...")
        self.update_idletasks()
        if not url:
            self.quality_combo['values'] = []
            self.quality_var.set('')
            return
        try:
            import yt_dlp
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                video_formats = []
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') in ('mp4', 'webm', 'mkv'):
                        height = f.get('height')
                        fps = f.get('fps')
                        ext = f.get('ext')
                        format_id = f.get('format_id')
                        note = f.get('format_note', '')
                        label = f"{format_id} - {height}p {note} {ext}"
                        video_formats.append(label)
                if video_formats:
                    self.quality_combo['values'] = video_formats
                    self.quality_var.set(video_formats[0])
                else:
                    self.quality_combo['values'] = ['best']
                    self.quality_var.set('best')
            self.status_label.config(text="Available qualities updated.")
        except Exception:
            self.quality_combo['values'] = ['best']
            self.quality_var.set('best')
            self.status_label.config(text="Could not fetch video qualities.")

    def _start_download(self) -> None:
        url = self.url_var.get().strip()
        output = self.output_var.get().strip()
        is_youtube = self.youtube_var.get()
        no_resume = self.no_resume_var.get()

        # Auto-detect output filename if not provided
        if not output:
            try:
                import mimetypes
                import os
                from urllib.parse import urlparse
                import requests
                if is_youtube:
                    import yt_dlp
                    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                        info = ydl.extract_info(url, download=False)
                        title = info.get('title', 'youtube_video')
                        ext = info.get('ext', 'mp4')
                        basename = f"{title}.{ext}"
                else:
                    basename = os.path.basename(urlparse(url).path)
                    if not basename or '.' not in basename:
                        resp = requests.head(url, allow_redirects=True, timeout=5)
                        content_type = resp.headers.get('content-type', '').split(';')[0]
                        ext = mimetypes.guess_extension(content_type) or ''
                        basename = 'downloaded_file' + ext
                output = basename
                self.output_var.set(output)
            except Exception:
                output = 'downloaded_file'
                self.output_var.set(output)

        self.progress["value"] = 0
        self.progress["maximum"] = 100
        self.status_label.config(text="Starting...")
        self._set_download_button_state(False)
        self.pause_btn['state'] = tk.NORMAL
        self.pause_btn['text'] = 'Pause'
        self.cancel_btn['state'] = tk.NORMAL
        self.cancel_event.clear()
        self.pause_event.set()  # Not paused by default
        self._is_downloading = True

        thread = threading.Thread(
            target=self._download_with_error_handling, args=(url, output, is_youtube, no_resume), daemon=True
        )
        thread.start()

    def _toggle_pause(self):
        if not self._is_downloading:
            return
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_btn['text'] = 'Resume'
            self.status_label.config(text="Paused")
        else:
            self.pause_event.set()
            self.pause_btn['text'] = 'Pause'

    def _cancel_download(self):
        if self._is_downloading:
            self.cancel_event.set()
            self.status_label.config(text="Cancelling download...")

    def _set_download_button_state(self, enabled: bool) -> None:
        self.download_btn['state'] = tk.NORMAL if enabled else tk.DISABLED

    def _download_with_error_handling(self, url, output, is_youtube, no_resume):
        try:
            self._download(url, output, is_youtube, no_resume)
        except Exception as e:
            self.after(0, self._download_done, False, str(e))

    def _download(self, url: str, output: str, is_youtube: bool, no_resume: bool) -> None:
        def progress_callback(downloaded, total):
            import time
            # Check for cancel before updating progress
            if self.cancel_event.is_set():
                raise Exception("Download cancelled by user.")
            while not self.pause_event.is_set():
                if self.cancel_event.is_set():
                    raise Exception("Download cancelled by user.")
                time.sleep(0.1)
            if self.cancel_event.is_set():
                raise Exception("Download cancelled by user.")
            self._progress_callback(downloaded, total)

        cancelled = False
        success = False
        try:
            if is_youtube:
                import re
                match = re.match(r"(\d+)", self.quality_var.get())
                format_id = match.group(1) if match else 'best'
                def yt_progress_hook(d):
                    if self.cancel_event.is_set():
                        raise Exception("Download cancelled by user.")
                    if d.get('status') == 'downloading':
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                        progress_callback(downloaded, total)
                    elif d.get('status') == 'finished':
                        total = d.get('total_bytes') or d.get('total_bytes_estimate') or d.get('downloaded_bytes', 0)
                        progress_callback(total, total)
                ydl_opts = {
                    'format': format_id,
                    'progress_hooks': [yt_progress_hook],
                    'outtmpl': output
                }
                import yt_dlp
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                success = True
            else:
                # For file downloads, we must chunk the download and check cancel/pause between chunks
                import requests
                import os
                from tqdm import tqdm
                headers = {}
                initial_pos = 0
                if os.path.exists(output) and not no_resume:
                    initial_pos = os.path.getsize(output)
                    headers['Range'] = f'bytes={initial_pos}-'
                resp = requests.get(url, stream=True, headers=headers)
                total = int(resp.headers.get('content-length', 0))
                mode = 'ab' if initial_pos > 0 else 'wb'
                downloaded = initial_pos
                chunk_size = 1024 * 32
                with open(output, mode) as f:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if self.cancel_event.is_set():
                            raise Exception("Download cancelled by user.")
                        while not self.pause_event.is_set():
                            if self.cancel_event.is_set():
                                raise Exception("Download cancelled by user.")
                            time.sleep(0.1)
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress_callback(downloaded, total)
                success = True
        except Exception as e:
            if str(e) == "Download cancelled by user.":
                cancelled = True
            else:
                import traceback
                print(traceback.format_exc())
        if cancelled:
            self.after(0, self._download_cancelled)
        else:
            self.after(0, self._download_done, success, None)

    def _download_cancelled(self):
        self._set_download_button_state(True)
        self.pause_btn['state'] = tk.DISABLED
        self.cancel_btn['state'] = tk.DISABLED
        self._is_downloading = False
        self.status_label.config(text="Download cancelled.")
        messagebox.showinfo("Download", "Download cancelled by user.")
        self._progress_stats = None

    def _progress_callback(self, downloaded: int, total: int) -> None:
        import time
        if not self._progress_stats:
            self._progress_stats = {
                'start_time': time.time(),
                'last_time': time.time(),
                'last_downloaded': 0,
                'speed': 0,
                'eta': None
            }
        stats = self._progress_stats
        now = time.time()
        elapsed = now - stats['start_time']
        recent_elapsed = now - stats['last_time']
        recent_bytes = downloaded - stats['last_downloaded']
        if recent_elapsed > 0:
            speed = recent_bytes / recent_elapsed
        else:
            speed = stats['speed']
        stats['speed'] = speed
        stats['last_time'] = now
        stats['last_downloaded'] = downloaded
        if total > 0 and speed > 0:
            eta = (total - downloaded) / speed
        else:
            eta = None
        stats['eta'] = eta
        percent = (downloaded / total * 100) if total > 0 else 0
        self.after(0, self._update_progress, downloaded, total, percent, speed, eta)

    def _update_progress(self, downloaded: int, total: int, percent: float, speed: float, eta: float) -> None:
        def format_bytes(num):
            for unit in ['B','KB','MB','GB','TB']:
                if num < 1024.0:
                    return f"{num:.2f} {unit}"
                num /= 1024.0
            return f"{num:.2f} PB"
        def format_time(seconds):
            if seconds is None or seconds == float('inf'):
                return 'N/A'
            m, s = divmod(int(seconds), 60)
            h, m = divmod(m, 60)
            if h:
                return f"{h}h {m}m {s}s"
            elif m:
                return f"{m}m {s}s"
            else:
                return f"{s}s"
        if total > 0:
            self.progress["maximum"] = total
            self.progress["value"] = downloaded
            speed_str = format_bytes(speed) + "/s" if speed else "N/A"
            eta_str = format_time(eta)
            self.status_label.config(
                text=f"{percent:.1f}% | {format_bytes(downloaded)} / {format_bytes(total)} | {speed_str} | ETA: {eta_str}"
            )
        else:
            # Indeterminate mode for unknown total
            self.progress["maximum"] = 100
            # Use percent as a fallback, but if total is 0, show bytes
            if downloaded > 0:
                self.progress["value"] = min(100, percent)
            else:
                self.progress["value"] = 0
            speed_str = format_bytes(speed) + "/s" if speed else "N/A"
            self.status_label.config(
                text=f"{format_bytes(downloaded)} | {speed_str}"
            )

    def _download_done(self, success: bool, error: str = None) -> None:
        import os
        self._set_download_button_state(True)
        self.pause_btn['state'] = tk.DISABLED
        self.cancel_btn['state'] = tk.DISABLED
        self._is_downloading = False
        # Reset progress stats
        self._progress_stats = None
        if success:
            self.progress["value"] = self.progress["maximum"]
            self.status_label.config(text="Download complete!")
            file_path = os.path.abspath(self.output_var.get())
            file_dir = os.path.dirname(file_path)
            def open_file():
                os.startfile(file_path)
            def open_folder():
                os.startfile(file_dir)
            msg_box = tk.Toplevel(self)
            msg_box.title("Download completed")
            tk.Label(msg_box, text="Download completed!").pack(padx=10, pady=10)
            tk.Button(msg_box, text="Open File", command=lambda: [open_file(), msg_box.destroy()]).pack(side=tk.LEFT, padx=10, pady=10)
            tk.Button(msg_box, text="Open Folder", command=lambda: [open_folder(), msg_box.destroy()]).pack(side=tk.LEFT, padx=10, pady=10)
            tk.Button(msg_box, text="Close", command=msg_box.destroy).pack(side=tk.LEFT, padx=10, pady=10)
        else:
            self.status_label.config(text="Download failed")
            msg = f"Download failed"
            if error:
                msg += f": {error}"
            messagebox.showerror("Download", msg)

if __name__ == "__main__":
    app = DownloaderGUI()
    app.mainloop()