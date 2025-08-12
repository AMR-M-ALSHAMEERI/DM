"""
File Downloader with Resume & YouTube Support
CS50P Final Project

Features:
- File downloads with resume capability
- YouTube video downloads
- Progress tracking
- URL validation
"""


import argparse
import os
import requests
from urllib.parse import urlparse
from typing import Callable, Optional, Tuple
import mimetypes
import yt_dlp
from tqdm import tqdm


def main() -> int:
    """
    Main entry point for the file downloader program.
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Download files or YouTube videos with resume capability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Regular file: python project.py https://example.com/file.txt
  YouTube: python project.py --youtube https://youtube.com/watch?v=ID 
        """
    )
    parser.add_argument("url", help="URL to download from")
    parser.add_argument("-o", "--output", help="Output filename")
    parser.add_argument(
        "--youtube", 
        action="store_true", 
        help="Use YouTube download mode"
    )

    args = parser.parse_args()

    try:
        if args.youtube:
            success = download_youtube(args.url)
        else:
            # Provide default resume=True, as there is no args.no_resume
            success = download_file(
                args.url,
                args.output,
                resume=True
            )
        if not success:
            return 1
        return 0
    except KeyboardInterrupt:
        print("\nDownload cancelled by user")
        return 1

def _validate_file_size(size: int) -> bool:
    """Check if file size is within reasonable limits (< 10GB)"""
    MAX_SIZE = 10 * 1024 * 1024 * 1024  # 10GB
    return 0 < size < MAX_SIZE

    # (Removed duplicate definition)
def _get_remote_file_info(url: str) -> Tuple[int, str]:
    """Helper function to get file size and content type"""
    try:
        response = requests.head(url, allow_redirects=True)
        size = int(response.headers.get('content-length', 0))
        if size and not _validate_file_size(size):
            raise ValueError("File size too large (max 10GB)")
        content_type = response.headers.get('content-type', '').lower()
        return size, content_type
    except requests.RequestException:
        # If HEAD request fails, return defaults so download can continue
        return 0, ''

def download_file(
    url: str,
    filename: str = None,
    resume: bool = True,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> bool:
    """
    Download a file from the given URL with resume capability.
    
    Args:
        url: URL to download from
        filename: Optional custom filename to save as
        resume: Whether to attempt resuming partial downloads
        
    Returns:
        bool: True if download successful, False otherwise
        
    Raises:
        ValueError: If file size exceeds limit
    """
    try:
        if not validate_url(url):
            print(f"Invalid or inaccessible URL: {url}")
            return False
            
        # Get file info with size validation
        try:
            total_size, content_type = _get_remote_file_info(url)
        except ValueError as e:
            print(f"Error: {str(e)}")
            return False
            
        if 'text/html' in content_type:
            print("Error: URL points to a webpage, not a downloadable file")
            return False
            
        # Generate filename if needed
        if filename is None:
            ext = mimetypes.guess_extension(content_type) or ''
            filename = os.path.basename(url.split('?')[0]) or f'downloaded_file{ext}'
        
        # Check if we can resume
        initial_pos = 0
        if os.path.exists(filename) and resume:
            initial_pos = os.path.getsize(filename)
            if total_size > 0 and initial_pos >= total_size:
                print(f"File {filename} is already fully downloaded")
                return True
            
            headers = {'Range': f'bytes={initial_pos}-'}
            mode = 'ab'  # Append mode for resume
        else:
            if os.path.exists(filename):
                response = input(f"File {filename} exists. Overwrite? (y/n): ")
                if response.lower() != 'y':
                    print("Download cancelled")
                    return False
            headers = {}
            mode = 'wb'  # Write mode for fresh download
            
        # Start download
        response = requests.get(url, stream=True, headers=headers)
        
        if resume and response.status_code == 206:  # Partial content
            print(f"Resuming download from {initial_pos} bytes")
        elif resume and initial_pos > 0:
            print("Resume not supported by server, starting fresh download")
            initial_pos = 0
            mode = 'wb'
            
        # Download with progress bar
        with open(filename, mode) as file, \
             tqdm(
                 desc=filename,
                 initial=initial_pos,
                 total=total_size,
                 unit='iB',
                 unit_scale=True,
                 unit_divisor=1024,
             ) as progress_bar:
            
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                progress_bar.update(size)
        if progress_callback:
            downloaded = initial_pos
            with open(filename, mode) as file:
                for data in response.iter_content(chunk_size=1024):
                    size = file.write(data)
                    downloaded += size
                    progress_callback(downloaded, total_size)
            # Ensure completion is reported
            progress_callback(total_size, total_size)
        else:
            with open(filename, mode) as file, \
                 tqdm(
                     desc=filename,
                     initial=initial_pos,
                     total=total_size,
                     unit='iB',
                     unit_scale=True,
                     unit_divisor=1024,
                 ) as progress_bar:
                for data in response.iter_content(chunk_size=1024):
                    size = file.write(data)
                    progress_bar.update(size)
        
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            print("Error: Download failed - empty or missing file")
            return False
                
        return True
        
    except requests.RequestException as e:
        print(f"Network error during download: {str(e)}")
        return False
    except IOError as e:
        print(f"File error during download: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error during download: {str(e)}")
        return False



    # (Removed duplicate definition)
def download_youtube(
    url: str, progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    """
    Download a YouTube video at best available quality.
    """
    try:
        # Validate YouTube URL
        if not validate_url(url) or 'youtube.com' not in url:
            print("Invalid YouTube URL")
            return False

        def hook(d):
            if progress_callback:
                if d.get('status') == 'downloading':
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    progress_callback(downloaded, total)
                elif d.get('status') == 'finished':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or d.get('downloaded_bytes', 0)
                    progress_callback(total, total)
            _youtube_progress_hook(d)

        ydl_opts = {
            'format': 'best',  # Use the best available format with both video and audio
            'progress_hooks': [hook],
            'outtmpl': '%(title)s.%(ext)s'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Downloading video in best available quality...")
            ydl.download([url])

        return True

    except Exception as e:
        print(f"YouTube download failed: {str(e)}")
        return False


def _youtube_progress_hook(d):
    """Helper function to display YouTube download progress"""
    if d['status'] == 'downloading':
        percentage = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        print(f"\rDownloading... {percentage} at {speed} (ETA: {eta})", end='')
    elif d['status'] == 'finished':
        print("\nDownload complete! Converting format...")

def validate_url(url: str) -> bool:
    """
    Validate if a given URL is properly formatted and accessible.
    """
    try:
        result = urlparse(url)
        is_valid = all([result.scheme, result.netloc])
        if not is_valid:
            return False
        if result.scheme not in ['http', 'https']:
            return False
        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            # Treat common success codes and "forbidden" (403) as valid to handle
            # environments where HEAD requests are blocked but the URL exists.
            return response.status_code in [200, 206, 403]
        except requests.RequestException:
            # Assume URL is valid if format is correct but network is unavailable
            return True
    except ValueError:
        return False



if __name__ == "__main__":
    main()
