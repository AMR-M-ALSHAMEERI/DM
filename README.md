# File Downloader with Resume & YouTube Support
#### Video Demo: <INSERT_YOUTUBE_VIDEO_URL_HERE>
#### Description:

This project is a Python-based command-line tool that allows users to download regular files and YouTube videos with support for resuming incomplete downloads. It was developed as a final project for CS50’s Introduction to Programming with Python (CS50P).

The tool provides a robust and user-friendly interface for downloading files with additional features such as:

- Resume capability for large or interrupted downloads  
- Real-time download progress with ETA using `tqdm`  
- YouTube video download support using `yt-dlp`  
- Smart URL validation before downloading  
- Clear error handling for network and file-related issues  

---

## Project Structure

### `project.py`

This is the main program file. It includes:

- `main()`: Parses command-line arguments and initiates the appropriate download mode (file or YouTube).
- `download_file(url, filename=None, resume=True)`: Handles file downloads from standard HTTP/HTTPS sources with resume support and a progress bar.
- `download_youtube(url)`: Downloads videos from YouTube using `yt-dlp` in the best available quality.
- `validate_url(url)`: Validates the format and accessibility of a given URL using `urllib.parse` and HTTP HEAD requests.
- `_get_remote_file_info(url)`: Retrieves the file size and content type from the response headers.
- `_validate_file_size(size)`: Ensures the file is within a 10GB limit.
- `_youtube_progress_hook(d)`: Displays download progress during YouTube downloads.


### `test_project.py`

This file contains unit tests using `pytest` and `unittest.mock` to ensure reliability across various scenarios. It tests:

- `validate_url()` for valid and invalid URLs
- `download_file()` including:
  - New downloads
  - Resumable downloads
  - Behavior when resume is unsupported
- `download_youtube()` including:
  - Valid and invalid URLs
  - Mocked `yt_dlp` behavior
- `main()` logic with command-line arguments
- `_validate_file_size()` for edge cases
- `_youtube_progress_hook()` output handling

All tests are isolated and clean up downloaded files after execution.

### `requirements.txt`

- requests
- yt-dlp
- tqdm
- pytest


---
## Installation

Install dependencies:

```bash
pip install -r requirements.txt

python project.py https://example.com/file.txt
python project.py https://example.com/file.txt -o custom_name.txt
python project.py https://example.com/file.txt --no-resume
```
YouTube Video Download
```bash
python project.py --youtube https://youtube.com/watch?v=VIDEO_ID
```

Options:

`url`: The file or video URL to download

`-o, --output`: Custom output filename

`--youtube`: Enable YouTube download mode

`--no-resume`: Disable resume capability