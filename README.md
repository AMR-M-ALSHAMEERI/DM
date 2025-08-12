gi# File Downloader & YouTube Downloader GUI

#### Video Demo: <INSERT_YOUTUBE_VIDEO_URL_HERE>

## Description

This project is a Python-based application with both a command-line and a graphical user interface (GUI) for downloading files and YouTube videos. It supports resuming, pausing, and cancelling downloads, and provides real-time progress, speed, and ETA information. The GUI is built with Tkinter and supports quality selection for YouTube videos.

---

## Features
- Download any file from a direct URL with resume, pause, and cancel support
- Download YouTube videos with quality selection (using `yt-dlp`)
- Real-time progress bar with percentage, speed, and ETA
- Automatic filename and filetype detection
- Open file or folder after download completes
- Smart URL validation and error handling

---

## Project Structure

- `project.py`: Core download logic for files and YouTube, used by both CLI and GUI
- `gui.py`: Tkinter-based GUI for user-friendly downloads
- `test_project.py`: Unit tests for core logic
- `requirements.txt`: All dependencies, version-pinned

---

## Installation

1. Clone the repository and navigate to the project folder.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. (Recommended for YouTube downloads) Install the ffmpeg binary and add it to your system PATH:
   - Download from: https://www.gyan.dev/ffmpeg/builds/
   - Extract and add the `bin` folder to your PATH

---

## Usage

### Command-Line

Download a file:
```bash
python project.py https://example.com/file.pdf
```

Download a file with custom name:
```bash
python project.py https://example.com/file.pdf -o myfile.pdf
```

Download a YouTube video:
```bash
python project.py --youtube https://youtube.com/watch?v=VIDEO_ID
```

### GUI

Run the GUI:
```bash
python gui.py
```

- Paste a URL and (optionally) select output file
- For YouTube, check "YouTube Mode" and select quality
- Use Pause/Resume and Cancel as needed
- When finished, use the Open File/Folder buttons

---

## Requirements

- Python 3.8+
- requests==2.32.4
- yt-dlp==2025.8.11
- tqdm==4.67.1
- ffmpeg-python==0.2.0

---

## Notes
- For best YouTube experience, install ffmpeg and add it to your PATH
- All downloads are resumable and cancellable from the GUI
- Tested on Windows (should work on Linux/Mac with minor tweaks)

---

## License
MIT