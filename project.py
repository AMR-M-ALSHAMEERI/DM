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
from typing import Optional, Tuple
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

    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Disable resume capability"
    )

    args = parser.parse_args()

    try:
        if args.youtube:
            success = download_youtube(args.url)
        else:
            success = download_file(
                args.url, 
                args.output, 
                resume=not args.no_resume
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

def _get_remote_file_info(url: str) -> Tuple[int, str]:
    """Helper function to get file size and content type"""
    response = requests.head(url, allow_redirects=True)
    size = int(response.headers.get('content-length', 0))
    if size and not _validate_file_size(size):
        raise ValueError("File size too large (max 10GB)")
    content_type = response.headers.get('content-type', '').lower()
    return size, content_type

def download_file(url: str, filename: str = None, resume: bool = True) -> bool:
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
            if initial_pos >= total_size:
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



def download_youtube(url: str) -> bool:
    """
    Download a YouTube video at best available quality.
    """
    try:
        # Validate YouTube URL
        if not validate_url(url) or 'youtube.com' not in url:
            print("Invalid YouTube URL")
            return False
            
        ydl_opts = {
            'format': 'best',  # Use the best available format with both video and audio
            'progress_hooks': [_youtube_progress_hook],
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
            
        response = requests.head(url, allow_redirects=True, timeout=5)
        # Ensure we return a boolean
        return response.status_code in [200, 206]
        
    except (requests.RequestException, ValueError):
        return False



if __name__ == "__main__":
    main()




