#!/usr/bin/env python3
"""
YouTube -> MP3  |  GUI Edition  v2
Requires: yt-dlp  ->  pip install yt-dlp
          ffmpeg  ->  brew/choco install ffmpeg  or  https://ffmpeg.org
"""

import os
import json
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont

# ── config ────────────────────────────────────────────────────────────────────
CONFIG_PATH = os.path.expanduser("~/.yt_to_mp3_config.json")

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(data: dict):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass  # best-effort


# ── dependency check ──────────────────────────────────────────────────────────
def check_deps():
    missing = []
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        missing.append("yt-dlp  (pip install yt-dlp)")
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        missing.append("ffmpeg  (brew/choco install ffmpeg  or  ffmpeg.org)")
    return missing


# ── colours ───────────────────────────────────────────────────────────────────
BG       = "#0f0f0f"
PANEL    = "#1a1a1a"
BORDER   = "#2a2a2a"
RED      = "#e63946"
RED_DARK = "#c1121f"
TEXT     = "#f1f1f1"
MUTED    = "#888888"
SUCCESS  = "#57cc99"
WARN     = "#ffd166"
CANCEL_C = "#aaaaaa"

PENDING     = "PENDING"
DOWNLOADING = "DOWNLOADING"
DONE        = "DONE"
ERROR       = "ERROR"
CANCELLED   = "CANCELLED"

STATUS_COLOUR = {
    PENDING:     MUTED,
    DOWNLOADING: WARN,
    DONE:        SUCCESS,
    ERROR:       RED,
    CANCELLED:   CANCEL_C,
}
STATUS_ICON = {
    PENDING:     "o",
    DOWNLOADING: ">",
    DONE:        "v",
    ERROR:       "x",
    CANCELLED:   "-",
}


# ── app ───────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YT -> MP3")
        self.resizable(False, False)
        self.configure(bg=BG)

        # fonts
        self.f_title = tkfont.Font(family="Courier New", size=18, weight="bold")
        self.f_sub   = tkfont.Font(family="Courier New", size=8)
        self.f_label = tkfont.Font(family="Courier New", size=9)
        self.f_mono  = tkfont.Font(family="Courier New", size=9)
        self.f_bold  = tkfont.Font(family="Courier New", size=11, weight="bold")

        # load saved config
        cfg = load_config()
        self.dir_var     = tk.StringVar(value=cfg.get("output_dir", os.path.expanduser("~")))
        self.quality_var = tk.StringVar(value=cfg.get("quality", "192"))

        # persist settings on change
        self.dir_var.trace_add("write",     lambda *_: self._save_config())
        self.quality_var.trace_add("write", lambda *_: self._save_config())

        # runtime state
        self._cancel_flag = threading.Event()
        self._downloading = False
        self._queue       = []

        self._build_ui()

        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── config ────────────────────────────────────────────────────────────────
    def _save_config(self):
        save_config({"output_dir": self.dir_var.get(), "quality": self.quality_var.get()})

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # header
        hdr = tk.Frame(self, bg=BG, padx=32, pady=24)
        hdr.grid(row=0, column=0, sticky="ew")
        tk.Label(hdr, text="YT->MP3", font=self.f_title, fg=RED, bg=BG).pack(anchor="w")
        tk.Label(hdr, text="paste a youtube link. get an mp3.", font=self.f_sub,
                 fg=MUTED, bg=BG).pack(anchor="w", pady=(2, 0))

        tk.Frame(self, bg=BORDER, height=1).grid(row=1, column=0, sticky="ew")

        # form
        form = tk.Frame(self, bg=BG, padx=32, pady=28)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(0, weight=1)

        # URL input + add button
        url_frame = tk.Frame(form, bg=BG)
        url_frame.pack(fill="x", pady=(0, 10))
        self._field_label(url_frame, "YOUTUBE URL")
        url_row = tk.Frame(url_frame, bg=BG)
        url_row.pack(fill="x")
        url_row.columnconfigure(0, weight=1)
        self.url_var = tk.StringVar()
        url_entry = self._make_entry(url_row, self.url_var)
        url_entry.grid(row=0, column=0, sticky="ew", ipady=8, ipadx=8)
        url_entry.bind("<Return>", lambda e: self._add_to_queue())
        tk.Button(
            url_row, text="  ADD  ", font=self.f_label,
            fg=TEXT, bg=BORDER, activeforeground=TEXT, activebackground="#333",
            relief="flat", bd=0, cursor="hand2", command=self._add_to_queue
        ).grid(row=0, column=1, padx=(8, 0), ipady=8, ipadx=4)

        # queue list
        queue_outer = tk.Frame(form, bg=BG)
        queue_outer.pack(fill="x", pady=(12, 0))
        self._field_label(queue_outer, "QUEUE")

        canvas_wrap = tk.Frame(queue_outer, bg=PANEL, highlightthickness=1,
                               highlightbackground=BORDER)
        canvas_wrap.pack(fill="x")
        self.q_canvas = tk.Canvas(canvas_wrap, bg=PANEL, highlightthickness=0,
                                  height=130, width=500)
        scrollbar = tk.Scrollbar(canvas_wrap, orient="vertical",
                                 command=self.q_canvas.yview)
        self.q_canvas.configure(yscrollcommand=scrollbar.set)
        self.q_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.q_inner = tk.Frame(self.q_canvas, bg=PANEL)
        self._cwin = self.q_canvas.create_window((0, 0), window=self.q_inner, anchor="nw")
        self.q_inner.bind("<Configure>",  lambda e: self.q_canvas.configure(
            scrollregion=self.q_canvas.bbox("all")))
        self.q_canvas.bind("<Configure>", lambda e: self.q_canvas.itemconfig(
            self._cwin, width=e.width))

        self._empty_lbl = tk.Label(self.q_inner, text="no urls added yet.",
                                   font=self.f_sub, fg=MUTED, bg=PANEL, pady=12)
        self._empty_lbl.pack(anchor="w", padx=12)

        # output folder
        out_frame = tk.Frame(form, bg=BG)
        out_frame.pack(fill="x", pady=(18, 10))
        self._field_label(out_frame, "OUTPUT FOLDER")
        out_row = tk.Frame(out_frame, bg=BG)
        out_row.pack(fill="x")
        out_row.columnconfigure(0, weight=1)
        self._make_entry(out_row, self.dir_var, width=44).grid(
            row=0, column=0, sticky="ew", ipady=8, ipadx=8)
        tk.Button(
            out_row, text="  BROWSE  ", font=self.f_label,
            fg=TEXT, bg=BORDER, activeforeground=TEXT, activebackground="#333",
            relief="flat", bd=0, cursor="hand2", command=self._browse
        ).grid(row=0, column=1, padx=(8, 0), ipady=8, ipadx=4)

        # bitrate
        q_frame = tk.Frame(form, bg=BG)
        q_frame.pack(fill="x", pady=(0, 24))
        self._field_label(q_frame, "BITRATE")
        btn_row = tk.Frame(q_frame, bg=BG)
        btn_row.pack(anchor="w")
        for kbps in ("128", "192", "256", "320"):
            self._radio_btn(btn_row, kbps)

        # convert + cancel buttons
        btn_frame = tk.Frame(form, bg=BG)
        btn_frame.pack(fill="x")
        btn_frame.columnconfigure(0, weight=1)

        self.go_btn = tk.Button(
            btn_frame, text="  CONVERT QUEUE  ",
            font=self.f_bold, fg=TEXT, bg=RED,
            activeforeground=TEXT, activebackground=RED_DARK,
            relief="flat", bd=0, cursor="hand2", command=self._start_queue
        )
        self.go_btn.grid(row=0, column=0, sticky="ew", ipady=12)
        self.go_btn.bind("<Enter>", lambda e: self.go_btn.configure(bg=RED_DARK))
        self.go_btn.bind("<Leave>", lambda e: self.go_btn.configure(bg=RED))

        self.cancel_btn = tk.Button(
            btn_frame, text="  CANCEL  ",
            font=self.f_bold, fg=MUTED, bg=BORDER,
            activeforeground=TEXT, activebackground="#333",
            relief="flat", bd=0, cursor="hand2",
            state="disabled", command=self._request_cancel
        )
        self.cancel_btn.grid(row=0, column=1, padx=(8, 0), ipady=12, ipadx=8)

        tk.Frame(self, bg=BORDER, height=1).grid(row=3, column=0, sticky="ew")

        # log
        log_frame = tk.Frame(self, bg=BG, padx=32, pady=16)
        log_frame.grid(row=4, column=0, sticky="ew")
        self.log = tk.Text(
            log_frame, font=self.f_mono, fg=MUTED, bg=PANEL,
            relief="flat", bd=0, highlightthickness=1, highlightbackground=BORDER,
            width=58, height=5, state="disabled", wrap="word", cursor="arrow"
        )
        self.log.pack(fill="x", ipady=8, ipadx=8)

        tk.Label(self, text="powered by yt-dlp + ffmpeg",
                 font=self.f_sub, fg="#444", bg=BG).grid(row=5, column=0, pady=(0, 14))

        self._log("ready. add urls to the queue and hit convert.", MUTED)

    # ── widget helpers ────────────────────────────────────────────────────────
    def _field_label(self, parent, text):
        tk.Label(parent, text=text, font=self.f_label,
                 fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 4))

    def _make_entry(self, parent, textvariable=None, width=52):
        e = tk.Entry(
            parent, textvariable=textvariable, font=self.f_mono,
            fg=TEXT, bg=PANEL, insertbackground=RED,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=RED, width=width
        )
        e.bind("<FocusIn>",  lambda ev: e.configure(highlightbackground=RED))
        e.bind("<FocusOut>", lambda ev: e.configure(highlightbackground=BORDER))
        return e

    def _radio_btn(self, parent, value):
        btn = tk.Radiobutton(
            parent, text=f"{value}k",
            variable=self.quality_var, value=value,
            font=self.f_label,
            fg=TEXT if value == self.quality_var.get() else MUTED,
            bg=BG, activebackground=BG, activeforeground=TEXT,
            selectcolor=BG, indicatoron=False,
            relief="flat", bd=0, padx=12, pady=6, cursor="hand2"
        )
        btn.pack(side="left", padx=(0, 6))

        def _style(*_):
            for w in parent.winfo_children():
                if isinstance(w, tk.Radiobutton):
                    w.configure(fg=TEXT if w.cget("text").replace("k", "") == self.quality_var.get() else MUTED)
        self.quality_var.trace_add("write", _style)

    # ── log ───────────────────────────────────────────────────────────────────
    def _log(self, msg, colour=TEXT):
        self.log.configure(state="normal")
        tag = f"t{colour.replace('#', '')}"
        self.log.tag_config(tag, foreground=colour)
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    # ── browse ────────────────────────────────────────────────────────────────
    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    # ── queue management ──────────────────────────────────────────────────────
    def _add_to_queue(self):
        url = self.url_var.get().strip()
        if not url:
            return
        if any(i["url"] == url for i in self._queue):
            messagebox.showinfo("Already added", "That URL is already in the queue.")
            return

        self._empty_lbl.pack_forget()

        row = tk.Frame(self.q_inner, bg=PANEL)
        row.pack(fill="x", padx=8, pady=4)

        status_lbl = tk.Label(
            row, text=f"{STATUS_ICON[PENDING]}  {PENDING}",
            font=self.f_sub, fg=STATUS_COLOUR[PENDING], bg=PANEL, width=14, anchor="w"
        )
        status_lbl.pack(side="left")

        tk.Label(
            row, text=url[:55] + ("..." if len(url) > 55 else ""),
            font=self.f_mono, fg=MUTED, bg=PANEL, anchor="w"
        ).pack(side="left", fill="x", expand=True)

        item = {"url": url, "status": PENDING, "row": row, "label": status_lbl}
        self._queue.append(item)

        tk.Button(
            row, text="x", font=self.f_sub,
            fg=MUTED, bg=PANEL, activeforeground=RED, activebackground=PANEL,
            relief="flat", bd=0, cursor="hand2",
            command=lambda i=item: self._remove_item(i)
        ).pack(side="right", padx=(4, 0))

        self.url_var.set("")

    def _remove_item(self, item):
        if item["status"] == DOWNLOADING:
            return
        item["row"].destroy()
        self._queue.remove(item)
        if not self._queue:
            self._empty_lbl.pack(anchor="w", padx=12)

    def _set_status(self, item, status):
        item["status"] = status
        item["label"].configure(
            text=f"{STATUS_ICON[status]}  {status}",
            fg=STATUS_COLOUR[status]
        )

    # ── cancel ────────────────────────────────────────────────────────────────
    def _request_cancel(self):
        self._cancel_flag.set()
        self._log("cancelling current download...", WARN)
        self.cancel_btn.configure(state="disabled")

    # ── convert ───────────────────────────────────────────────────────────────
    def _start_queue(self):
        if self._downloading:
            return

        pending = [i for i in self._queue if i["status"] == PENDING]
        if not pending:
            messagebox.showinfo("Nothing to do", "Add some URLs to the queue first.")
            return

        missing = check_deps()
        if missing:
            messagebox.showerror(
                "Missing dependencies",
                "Install the following:\n\n" + "\n".join(missing)
            )
            return

        self._downloading = True
        self._cancel_flag.clear()
        self._clear_log()
        self.go_btn.configure(text="  CONVERTING...  ", state="disabled", bg="#555")
        self.go_btn.unbind("<Enter>")
        self.go_btn.unbind("<Leave>")
        self.cancel_btn.configure(state="normal", fg=TEXT)

        threading.Thread(target=self._run_queue, args=(pending,), daemon=True).start()

    def _run_queue(self, items):
        for item in items:
            if self._cancel_flag.is_set():
                self.after(0, self._set_status, item, CANCELLED)
                continue

            self.after(0, self._set_status, item, DOWNLOADING)
            self.after(0, self._log, f"> {item['url'][:60]}", MUTED)

            success, result = self._download(item["url"])

            if not success and self._cancel_flag.is_set():
                self.after(0, self._set_status, item, CANCELLED)
                self.after(0, self._log, "- cancelled", CANCEL_C)
            elif success:
                self.after(0, self._set_status, item, DONE)
                self.after(0, self._log, f"done: {result}.mp3", SUCCESS)
            else:
                self.after(0, self._set_status, item, ERROR)
                self.after(0, self._log, f"error: {result}", RED)

        self.after(0, self._finish)

    def _download(self, url):
        """Returns (success: bool, title_or_error: str)"""
        import yt_dlp

        cancel   = self._cancel_flag
        out_dir  = self.dir_var.get()
        quality  = self.quality_var.get()

        class SilentLogger:
            def debug(self, msg):   pass
            def warning(self, msg): pass
            def error(self, msg):   pass

        def progress_hook(d):
            if cancel.is_set():
                raise yt_dlp.utils.DownloadCancelled()

        os.makedirs(out_dir, exist_ok=True)
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }],
            "logger": SilentLogger(),
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return True, info.get("title", "file")
        except yt_dlp.utils.DownloadCancelled:
            return False, "cancelled"
        except Exception as exc:
            return False, str(exc)

    def _finish(self):
        self._downloading = False
        self._cancel_flag.clear()

        self.go_btn.configure(text="  CONVERT QUEUE  ", state="normal", bg=RED)
        self.go_btn.bind("<Enter>", lambda e: self.go_btn.configure(bg=RED_DARK))
        self.go_btn.bind("<Leave>", lambda e: self.go_btn.configure(bg=RED))
        self.cancel_btn.configure(state="disabled", fg=MUTED)

        done      = sum(1 for i in self._queue if i["status"] == DONE)
        cancelled = sum(1 for i in self._queue if i["status"] == CANCELLED)
        errors    = sum(1 for i in self._queue if i["status"] == ERROR)
        self._log(f"\ndone: {done}  cancelled: {cancelled}  errors: {errors}", MUTED)


if __name__ == "__main__":
    app = App()
    app.mainloop()
