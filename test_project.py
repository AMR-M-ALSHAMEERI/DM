"""
Test suite for File Downloader project.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import requests
from project import (
    validate_url, 
    download_file, 
    download_youtube, 
    _validate_file_size,
    _youtube_progress_hook,
    main
)

@pytest.fixture
def mock_response():
    """Fixture for mocked responses"""
    response = MagicMock()
    response.status_code = 200
    response.headers = {
        'content-length': '1000',
        'content-type': 'text/plain'
    }
    # Add status_code property
    type(response).status_code = PropertyMock(return_value=200)
    return response

@pytest.fixture
def mock_head_request(mock_response):
    """Fixture for mocking head requests"""
    with patch('project.requests.head') as mock_head:
        mock_head.return_value = mock_response
        yield mock_head

@pytest.fixture
def mock_get_request(mock_response):
    """Fixture for mocking get requests"""
    with patch('project.requests.get') as mock_get:
        mock_get.return_value = mock_response
        mock_get.return_value.iter_content.return_value = [b'test data']
        yield mock_get

def test_validate_url(mock_head_request):
    """Test URL validation functionality"""
    mock_head_request.return_value.status_code = 200
    assert validate_url("https://www.example.com") == True
    assert validate_url("http://example.com/file.txt") == True
    
    # Test invalid URLs
    mock_head_request.side_effect = requests.RequestException()
    assert validate_url("not_a_url") == False

def test_download_file(mock_response):
    """Test file download functionality"""
    with patch('project.requests.head') as mock_head, \
         patch('project.requests.get') as mock_get:
        
        # Setup mocks
        mock_head.return_value = mock_response
        mock_get.return_value.status_code = 200
        mock_get.return_value.iter_content.return_value = [b'test data']
        
        result = download_file("https://getsamplefiles.com/download/txt/sample-1.txt", "test.txt")
        assert result == True
        if os.path.exists("test.txt"):
            os.remove("test.txt")

def test_download_file_resume(mock_response):
    """Test file download resume functionality"""
    with patch('project.requests.head') as mock_head, \
         patch('project.requests.get') as mock_get:
        
        # Setup mocks
        mock_head.return_value = mock_response
        mock_get.return_value.status_code = 206
        mock_get.return_value.iter_content.return_value = [b'test data']
        
        # Create partial file
        filename = "resume_test.txt"
        with open(filename, 'wb') as f:
            f.write(b'partial')
        
        result = download_file("https://getsamplefiles.com/download/txt/sample-1.txt", filename, resume=True)
        assert result == True
        os.remove(filename)


def test_download_youtube():
    """Test YouTube video download functionality"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        instance = mock_ydl.return_value.__enter__.return_value
        
        # Test with invalid URL
        with patch('project.validate_url', return_value=False):
            result = download_youtube("invalid_url")
            assert result == False
        
        with patch('project.validate_url', return_value=True):
            result = download_youtube("https://youtube.com/watch?v=test")
            assert result == True
            instance.download.assert_called_once()

def test_download_file_resume_supported(mock_head_request, mock_get_request):
    """Test resume when server supports it"""
    mock_get_request.return_value.status_code = 206
    result = download_file("https://getsamplefiles.com/download/txt/sample-1.txt", "partial.txt")
    assert result == True
    assert os.path.exists("partial.txt")
    os.remove("partial.txt")

def test_download_file_resume_unsupported(mock_response):
    """Test fallback when server doesn't support resume"""
    with patch('project.requests.head') as mock_head, \
         patch('project.requests.get') as mock_get:
        
        # Setup head request
        mock_head.return_value = mock_response
        mock_head.return_value.status_code = 200
        
        # Setup get request
        mock_get.return_value.status_code = 200
        mock_get.return_value.iter_content.return_value = [b'data']
        mock_get.return_value.headers = mock_response.headers
        
        result = download_file("https://getsamplefiles.com/download/txt/sample-1.txt", "full.txt")
        assert result == True
        assert os.path.exists("full.txt")
        os.remove("full.txt")


def test_main_file_download():
    """Test main function with file download"""
    test_args = ['project.py', 'https://example.com/file.txt']
    with patch.object(sys, 'argv', test_args), \
         patch('project.download_file', return_value=True) as mock_download:
        assert main() == 0
        mock_download.assert_called_once()

def test_main_youtube_download():
    """Test main function with YouTube download"""
    test_args = ['project.py', '--youtube', 'https://youtube.com/watch?v=test']
    with patch.object(sys, 'argv', test_args), \
         patch('project.download_youtube', return_value=True) as mock_yt:
        assert main() == 0
        mock_yt.assert_called_once()


def test_file_size_validation():
    """Test file size validation"""
    assert _validate_file_size(1000) == True  # 1KB
    assert _validate_file_size(1024 * 1024 * 1024) == True  # 1GB
    assert _validate_file_size(15 * 1024 * 1024 * 1024) == False  # 15GB
    assert _validate_file_size(0) == False  # Empty file
    assert _validate_file_size(-1) == False  # Invalid size

def test_youtube_progress_hook():
    """Test YouTube progress hook display"""
    data = {
        'status': 'downloading',
        '_percent_str': '50.0%',
        '_speed_str': '1MB/s',
        '_eta_str': '30s'
    }
    _youtube_progress_hook(data)  # Should not raise exception

def test_url_validation():
    """Test URL validation"""
    # Valid URLs
    assert validate_url("https://getsamplefiles.com") == True
    assert validate_url("https://getsamplefiles.com/download/txt/sample-1.txt") == True
    
    # Invalid URLs
    assert validate_url("not_a_url") == False
    assert validate_url("ftp://example.com") == False
    assert validate_url("") == False

def test_file_download():
    """Test file download functionality"""
    with patch('requests.get') as mock_get:
        # Mock successful download
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {'content-length': '100', 'content-type': 'text/plain'}
        mock_get.return_value.iter_content.return_value = [b'test data']
        
        assert download_file("https://getsamplefiles.com/download/txt/sample-1.txt", "test.txt") == True
        if os.path.exists("test.txt"):
            os.remove("test.txt")


def test_youtube_download():
    """Test YouTube download functionality"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        instance = mock_ydl.return_value.__enter__.return_value
        instance.download.return_value = None
        
        assert download_youtube("https://youtube.com/watch?v=test") == True
