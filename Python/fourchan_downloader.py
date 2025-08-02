#!/usr/bin/env python3
"""
4chan Thread Image Downloader

Downloads all full-sized images from a 4chan thread to a local directory.
Usage: python script.py <thread_url>
Example: python script.py https://boards.4chan.org/g/thread/12345678
"""

import os
import sys
import re
import requests
import json
from urllib.parse import urlparse
from pathlib import Path


def extract_board_and_thread(url):
    """Extract board name and thread number from 4chan URL"""
    pattern = r'https?://boards\.4chan\.org/([^/]+)/thread/(\d+)'
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid 4chan thread URL format")
    return match.group(1), match.group(2)


def get_thread_data(board, thread_no):
    """Fetch thread data from 4chan API"""
    api_url = f"https://a.4cdn.org/{board}/thread/{thread_no}.json"
    
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch thread data: {e}")


def create_directory(thread_no):
    """Create directory for storing images"""
    dir_path = Path(f"images/{thread_no}")
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def download_image(url, filepath):
    """Download a single image"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <4chan_thread_url>")
        print("Example: python script.py https://boards.4chan.org/g/thread/12345678")
        sys.exit(1)
    
    thread_url = sys.argv[1]
    
    try:
        # Extract board and thread number from URL
        board, thread_no = extract_board_and_thread(thread_url)
        print(f"Board: /{board}/, Thread: {thread_no}")
        
        # Get thread data from API
        print("Fetching thread data...")
        thread_data = get_thread_data(board, thread_no)
        
        # Create output directory
        output_dir = create_directory(thread_no)
        print(f"Output directory: {output_dir}")
        
        # Extract posts with images
        posts = thread_data.get('posts', [])
        image_count = 0
        downloaded_count = 0
        
        for post in posts:
            # Check if post has an image
            if 'tim' in post and 'ext' in post:
                # Construct image URL
                tim = post['tim']  # Renamed filename (timestamp)
                ext = post['ext']  # File extension
                filename = post.get('filename', str(tim))  # Original filename
                
                # Full-sized image URL
                image_url = f"https://i.4cdn.org/{board}/{tim}{ext}"
                
                # Create safe filename
                safe_filename = f"{filename}_{tim}{ext}"
                # Remove invalid characters for filesystem
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', safe_filename)
                
                filepath = output_dir / safe_filename
                
                # Skip if file already exists
                if filepath.exists():
                    print(f"Skipping {safe_filename} (already exists)")
                    downloaded_count += 1
                    continue
                
                print(f"Downloading: {safe_filename}")
                if download_image(image_url, filepath):
                    downloaded_count += 1
                
                image_count += 1
        
        print(f"\nDownload complete!")
        print(f"Total images found: {image_count}")
        print(f"Successfully downloaded: {downloaded_count}")
        print(f"Images saved to: {output_dir}")
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
