# YT → MP3

A lightweight desktop app to convert YouTube videos to MP3 files.

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Screenshots

> GUI version running with a dark theme, URL input, folder picker, bitrate selector, and live log output.

## Features

- 🎵 Converts any YouTube video to MP3
- 🖥️ Clean dark-themed GUI (no terminal needed)
- 📁 Choose your output folder
- 🎚️ Bitrate options: 128 / 192 / 256 / 320 kbps
- 📋 Live log showing download progress

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

**GUI app**
```bash
python yt_to_mp3_gui.py
```

**Command-line version**
```bash
# Basic — saves to current folder
python yt_to_mp3.py https://www.youtube.com/watch?v=...

# Custom output folder + bitrate
python yt_to_mp3.py https://youtu.be/... -o ~/Music -q 320
```

### CLI options

| Flag | Description | Default |
|------|-------------|---------|
| `-o`, `--output` | Output directory | Current folder |
| `-q`, `--quality` | Bitrate in kbps (`128`, `192`, `256`, `320`) | `192` |

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
