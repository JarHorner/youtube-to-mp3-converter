# YT → MP3

A lightweight desktop app to convert YouTube videos to MP3 files.

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Screenshots

> GUI version with a dark theme, URL input, download queue, folder picker, bitrate selector, artist/title metadata fields, cancel button, and live log output.

## Features

- 🎵 Converts any YouTube video to MP3
- 🖥️ Clean dark-themed GUI (no terminal needed)
- 📁 Choose your output folder
- 🎚️ Bitrate options: 128 / 192 / 256 / 320 kbps
- 📋 Live log showing download progress
- 📜 Download queue — add multiple URLs and convert them in one go
- ⏹️ Cancel button — stop a download cleanly at any time
- 🏷️ Artist and Title metadata — embedded directly into the MP3's ID3 tags
- 💾 Settings are saved automatically between sessions

## Requirements

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/download.html)
- yt-dlp (see install steps below)

## Installation

**1. Clone the repo**
```bash
git clone https://github.com/your-username/yt-to-mp3.git
cd yt-to-mp3
```

**2. Install Python dependencies**
```bash
pip install -r requirements.txt
```

**3. Install ffmpeg**

| OS      | Command                          |
|---------|----------------------------------|
| macOS   | `brew install ffmpeg`            |
| Windows | `choco install ffmpeg`           |
| Linux   | `sudo apt install ffmpeg`        |

Or download directly from [ffmpeg.org](https://ffmpeg.org/download.html).

## Usage

```bash
python yt_to_mp3_gui.py
```

1. Paste a YouTube URL into the **URL field** and click **ADD** (or press Enter) to add it to the queue. Repeat for as many videos as you like.
2. Set your **output folder**, **bitrate**, and optionally an **Artist** and **Title** to embed as metadata — leave these blank to use the channel name and video title automatically.
3. Click **CONVERT QUEUE** to start. Each item in the queue will show its status as it progresses.
4. Use the **CANCEL** button at any time to stop the current download.

Your output folder and bitrate are saved automatically and restored on next launch.

## Building a Standalone Executable

You can package the app into a single `.exe` (Windows) so it can be run without Python installed.

**1. Install PyInstaller**
```bash
pip install pyinstaller
```

**2. Build the exe**
```bash
pyinstaller --onefile --windowed --name "YT-to-MP3" yt_to_mp3_gui.py
```

**3. Find your exe**

The finished executable will be in the `dist/` folder.

> **Note:** ffmpeg is not bundled — users will still need to install it separately (see Installation above).

## Troubleshooting

**The app suddenly stops working / videos won't download**

YouTube periodically changes how their site works, which can break yt-dlp. The fix is almost always:
```bash
pip install --upgrade yt-dlp
```

**ffmpeg not found**

Make sure ffmpeg is installed and accessible on your system PATH. You can verify with:
```bash
ffmpeg -version
```

## License

MIT — see [LICENSE](LICENSE) for details.
