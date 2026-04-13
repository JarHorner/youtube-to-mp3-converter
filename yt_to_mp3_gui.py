#!/usr/bin/env python3
"""
YouTube → MP3  |  GUI Edition
Requires: yt-dlp  →  pip install yt-dlp
          ffmpeg  →  brew/choco install ffmpeg  or  https://ffmpeg.org
"""

import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont

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


# ── colour palette ────────────────────────────────────────────────────────────
BG        = "#0f0f0f"
PANEL     = "#1a1a1a"
BORDER    = "#2a2a2a"
RED       = "#e63946"
RED_DARK  = "#c1121f"
TEXT      = "#f1f1f1"
MUTED     = "#888888"
SUCCESS   = "#57cc99"
WARN      = "#ffd166"


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("YT → MP3")
        self.resizable(False, False)
        self.configure(bg=BG)

        # ── fonts ─────────────────────────────────────────────────────────────
        bold_font   = tkfont.Font(family="Courier New", size=11, weight="bold")
        label_font  = tkfont.Font(family="Courier New", size=9)
        mono_font   = tkfont.Font(family="Courier New", size=9)
        title_font  = tkfont.Font(family="Courier New", size=18, weight="bold")
        sub_font    = tkfont.Font(family="Courier New", size=8)

        self._downloading = False

        # ── header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG, padx=32, pady=24)
        hdr.grid(row=0, column=0, sticky="ew")

        tk.Label(hdr, text="▶  YT→MP3", font=title_font,
                 fg=RED, bg=BG).pack(anchor="w")
        tk.Label(hdr, text="paste a youtube link. get an mp3.", font=sub_font,
                 fg=MUTED, bg=BG).pack(anchor="w", pady=(2, 0))

        # ── divider ───────────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).grid(row=1, column=0, sticky="ew")

        # ── main form ─────────────────────────────────────────────────────────
        form = tk.Frame(self, bg=BG, padx=32, pady=28)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(0, weight=1)

        def field_label(parent, text):
            tk.Label(parent, text=text, font=label_font,
                     fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 4))

        def entry_style(parent, textvariable=None, width=52):
            e = tk.Entry(
                parent, textvariable=textvariable,
                font=mono_font, fg=TEXT, bg=PANEL,
                insertbackground=RED,
                relief="flat", bd=0, highlightthickness=1,
                highlightbackground=BORDER, highlightcolor=RED,
                width=width
            )
            return e

        # URL
        url_frame = tk.Frame(form, bg=BG)
        url_frame.pack(fill="x", pady=(0, 18))
        field_label(url_frame, "YOUTUBE URL")
        self.url_var = tk.StringVar()
        url_entry = entry_style(url_frame, self.url_var)
        url_entry.pack(fill="x", ipady=8, ipadx=8)
        url_entry.bind("<FocusIn>",  lambda e: url_entry.configure(highlightbackground=RED))
        url_entry.bind("<FocusOut>", lambda e: url_entry.configure(highlightbackground=BORDER))

        # Output folder
        out_frame = tk.Frame(form, bg=BG)
        out_frame.pack(fill="x", pady=(0, 18))
        field_label(out_frame, "OUTPUT FOLDER")
        row = tk.Frame(out_frame, bg=BG)
        row.pack(fill="x")
        row.columnconfigure(0, weight=1)
        self.dir_var = tk.StringVar(value=os.path.expanduser("~"))
        dir_entry = entry_style(row, self.dir_var, width=44)
        dir_entry.grid(row=0, column=0, sticky="ew", ipady=8, ipadx=8)
        dir_entry.bind("<FocusIn>",  lambda e: dir_entry.configure(highlightbackground=RED))
        dir_entry.bind("<FocusOut>", lambda e: dir_entry.configure(highlightbackground=BORDER))

        browse_btn = tk.Button(
            row, text="  BROWSE  ", font=label_font,
            fg=TEXT, bg=BORDER, activeforeground=TEXT, activebackground="#333",
            relief="flat", bd=0, cursor="hand2",
            command=self._browse
        )
        browse_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0), ipady=8, ipadx=4)

        # Quality
        q_frame = tk.Frame(form, bg=BG)
        q_frame.pack(fill="x", pady=(0, 28))
        field_label(q_frame, "BITRATE")
        btn_row = tk.Frame(q_frame, bg=BG)
        btn_row.pack(anchor="w")

        self.quality_var = tk.StringVar(value="192")
        for kbps in ("128", "192", "256", "320"):
            self._radio_btn(btn_row, kbps)

        # Convert button
        self.go_btn = tk.Button(
            form,
            text="  CONVERT TO MP3  ",
            font=bold_font,
            fg=TEXT, bg=RED,
            activeforeground=TEXT, activebackground=RED_DARK,
            relief="flat", bd=0, cursor="hand2",
            command=self._start
        )
        self.go_btn.pack(fill="x", ipady=12)
        self.go_btn.bind("<Enter>", lambda e: self.go_btn.configure(bg=RED_DARK))
        self.go_btn.bind("<Leave>", lambda e: self.go_btn.configure(bg=RED))

        # ── divider ───────────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).grid(row=3, column=0, sticky="ew")

        # ── log panel ─────────────────────────────────────────────────────────
        log_frame = tk.Frame(self, bg=BG, padx=32, pady=16)
        log_frame.grid(row=4, column=0, sticky="ew")

        self.log = tk.Text(
            log_frame,
            font=mono_font, fg=MUTED, bg=PANEL,
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER,
            width=58, height=6,
            state="disabled", wrap="word",
            cursor="arrow"
        )
        self.log.pack(fill="x", ipady=8, ipadx=8)

        self._log("ready. paste a url and hit convert.", MUTED)

        # ── footer ────────────────────────────────────────────────────────────
        tk.Label(self, text="powered by yt-dlp + ffmpeg",
                 font=sub_font, fg="#444", bg=BG).grid(
            row=5, column=0, pady=(0, 14))

        # centre on screen
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── radio button helper ───────────────────────────────────────────────────
    def _radio_btn(self, parent, value):
        def on_enter(e, b=None): b.configure(fg=TEXT)
        def on_leave(e, b=None):
            b.configure(fg=TEXT if self.quality_var.get() == value else MUTED)

        btn = tk.Radiobutton(
            parent, text=f"{value}k",
            variable=self.quality_var, value=value,
            font=tkfont.Font(family="Courier New", size=9),
            fg=TEXT if value == "192" else MUTED,
            bg=BG, activebackground=BG, activeforeground=TEXT,
            selectcolor=BG,
            indicatoron=False,
            relief="flat", bd=0,
            padx=12, pady=6,
            cursor="hand2"
        )
        btn.pack(side="left", padx=(0, 6))
        btn.bind("<Enter>", lambda e, b=btn: on_enter(e, b))
        btn.bind("<Leave>", lambda e, b=btn: on_leave(e, b))

        def style_on_select(*_):
            for w in parent.winfo_children():
                if isinstance(w, tk.Radiobutton):
                    lbl = w.cget("text").replace("k", "")
                    w.configure(fg=TEXT if lbl == self.quality_var.get() else MUTED)
        self.quality_var.trace_add("write", style_on_select)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    def _log(self, msg, colour=TEXT):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n", colour)
        self.log.tag_config(colour, foreground=colour)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    # ── download logic ────────────────────────────────────────────────────────
    def _start(self):
        if self._downloading:
            return

        url = self.url_var.get().strip()
        out = self.dir_var.get().strip()
        quality = self.quality_var.get()

        if not url:
            messagebox.showwarning("Missing URL", "Please paste a YouTube URL.")
            return

        missing = check_deps()
        if missing:
            messagebox.showerror(
                "Missing dependencies",
                "Install the following before continuing:\n\n" + "\n".join(missing)
            )
            return

        self._downloading = True
        self.go_btn.configure(text="  CONVERTING…  ", state="disabled", bg="#555")
        self._clear_log()
        self._log(f"url     → {url[:60]}{'…' if len(url)>60 else ''}", MUTED)
        self._log(f"output  → {out}", MUTED)
        self._log(f"bitrate → {quality} kbps\n", MUTED)

        threading.Thread(target=self._run, args=(url, out, quality), daemon=True).start()

    def _run(self, url, out_dir, quality):
        import yt_dlp

        class LogSink:
            def __init__(self, app): self.app = app
            def debug(self, msg):
                if msg.startswith("[download]"):
                    self.app.after(0, lambda m=msg.strip(): self.app._log(m, MUTED))
            def warning(self, msg):
                self.app.after(0, lambda m=msg.strip(): self.app._log(f"⚠  {m}", WARN))
            def error(self, msg):
                self.app.after(0, lambda m=msg.strip(): self.app._log(f"✗  {m}", RED))

        os.makedirs(out_dir, exist_ok=True)

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }],
            "logger": LogSink(self),
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "file")
            self.after(0, self._done, title)
        except Exception as exc:
            self.after(0, self._error, str(exc))

    def _done(self, title):
        self._log(f"✓  {title}.mp3", SUCCESS)
        self._log("\nsaved to: " + self.dir_var.get(), MUTED)
        self._reset_btn()

    def _error(self, msg):
        self._log(f"\n✗  error: {msg}", RED)
        self._reset_btn()

    def _reset_btn(self):
        self._downloading = False
        self.go_btn.configure(
            text="  CONVERT TO MP3  ", state="normal", bg=RED)
        self.go_btn.bind("<Enter>", lambda e: self.go_btn.configure(bg=RED_DARK))
        self.go_btn.bind("<Leave>", lambda e: self.go_btn.configure(bg=RED))


if __name__ == "__main__":
    app = App()
    app.mainloop()
