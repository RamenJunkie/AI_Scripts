#!/usr/bin/env python3
"""
Bluesky Auto-Poster Script with Link Embeds and Featured Images

This script reads the first line from "topost.txt", posts it to Bluesky with
proper link embedding and featured image, removes it from the file, 
and appends it to "posted.txt".

Requirements:
- pip install atproto requests beautifulsoup4 pillow
- Set your Bluesky credentials in environment variables
"""

import os
import sys
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
from io import BytesIO
from PIL import Image
import tempfile

from atproto import Client, models
from bs4 import BeautifulSoup

# Configuration
BLUESKY_HANDLE = os.getenv('BLUESKY_HANDLE', 'your-handle.bsky.social')
BLUESKY_PASSWORD = os.getenv('BLUESKY_PASSWORD', 'your-app-password')
TOPOST_FILE = 'topost.txt'
POSTED_FILE = 'posted.txt'

# User agent for web scraping
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def read_first_line():
    """Read and return the first line from topost.txt"""
    try:
        with open(TOPOST_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("No content to post - topost.txt is empty")
            return None, []
        
        first_line = lines[0].strip()
        remaining_lines = lines[1:]
        
        return first_line, remaining_lines
    
    except FileNotFoundError:
        print(f"Error: {TOPOST_FILE} not found")
        return None, []
    except Exception as e:
        print(f"Error reading {TOPOST_FILE}: {e}")
        return None, []

def parse_line(line):
    """Parse a line into URL and comment"""
    if '|' not in line:
        print(f"Warning: Line doesn't contain '|' separator: {line}")
        return None, line.strip()
    
    parts = line.split('|', 1)
    url = parts[0].strip()
    comment = parts[1].strip()
    
    return url, comment

def fetch_page_metadata(url):
    """Fetch page title, description, and featured image from URL"""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Try Open Graph title first
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title.get('content').strip()
        
        # Get description
        description = None
        # Try Open Graph description first
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            description = og_desc.get('content').strip()
        else:
            # Try meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                description = meta_desc.get('content').strip()
        
        # Get featured image URL
        image_url = None
        # Try Open Graph image first
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = og_image.get('content').strip()
            # Make sure it's an absolute URL
            image_url = urljoin(url, image_url)
        
        # If no OG image, try Twitter card image
        if not image_url:
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                image_url = twitter_image.get('content').strip()
                image_url = urljoin(url, image_url)
        
        return {
            'title': title or url,
            'description': description or '',
            'image_url': image_url
        }
    
    except Exception as e:
        print(f"Error fetching metadata for {url}: {e}")
        return {
            'title': url,
            'description': '',
            'image_url': None
        }

def download_and_process_image(image_url):
    """Download image and process it for Bluesky upload"""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(image_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Open image with PIL
        img = Image.open(BytesIO(response.content))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large (Bluesky has size limits)
        max_size = (1200, 1200)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    except Exception as e:
        print(f"Error downloading/processing image {image_url}: {e}")
        return None

def upload_image_to_bluesky(client, image_data):
    """Upload image to Bluesky and return blob reference"""
    try:
        blob = client.upload_blob(image_data)
        return blob
    except Exception as e:
        print(f"Error uploading image to Bluesky: {e}")
        return None

def create_post_with_embed(client, url, comment, metadata):
    """Create a Bluesky post with embedded link card"""
    try:
        # Create external embed
        external_embed = models.AppBskyEmbedExternal.External(
            uri=url,
            title=metadata['title'][:300],  # Bluesky has title limits
            description=metadata['description'][:1000] if metadata['description'] else ''
        )
        
        # Handle image if available
        if metadata['image_url']:
            print(f"Downloading featured image: {metadata['image_url']}")
            image_data = download_and_process_image(metadata['image_url'])
            
            if image_data:
                print("Uploading image to Bluesky...")
                blob = upload_image_to_bluesky(client, image_data)
                if blob:
                    external_embed.thumb = blob.blob
                    print("✓ Image uploaded successfully")
                else:
                    print("⚠️  Failed to upload image, posting without it")
            else:
                print("⚠️  Failed to download image, posting without it")
        
        # Create the embed
        embed = models.AppBskyEmbedExternal.Main(external=external_embed)
        
        # Create the post
        response = client.send_post(text=comment, embed=embed)
        return response
    
    except Exception as e:
        print(f"Error creating post with embed: {e}")
        return None

def update_files(posted_line, remaining_lines):
    """Update topost.txt and append to posted.txt"""
    try:
        # Write remaining lines back to topost.txt
        with open(TOPOST_FILE, 'w', encoding='utf-8') as f:
            f.writelines(remaining_lines)
        
        # Append posted line to posted.txt with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(POSTED_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {posted_line}\n")
        
        print(f"✓ Files updated successfully")
        
    except Exception as e:
        print(f"Error updating files: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("Bluesky Auto-Poster with Link Embeds Starting...")
    
    # Check credentials
    if BLUESKY_HANDLE == 'your-handle.bsky.social' or BLUESKY_PASSWORD == 'your-app-password':
        print("\n⚠️  Please set your Bluesky credentials:")
        print("   Set environment variables BLUESKY_HANDLE and BLUESKY_PASSWORD")
        print("   Or modify the script with your credentials")
        print("\n   Example:")
        print("   export BLUESKY_HANDLE='yourname.bsky.social'")
        print("   export BLUESKY_PASSWORD='your-app-password'")
        sys.exit(1)
    
    # Read first line from topost.txt
    line_to_post, remaining_lines = read_first_line()
    if not line_to_post:
        return
    
    print(f"Content to post: {line_to_post}")
    
    # Parse the line
    url, comment = parse_line(line_to_post)
    
    if not url:
        print("❌ No URL found in line")
        return
    
    print(f"URL: {url}")
    print(f"Comment: {comment}")
    
    # Fetch page metadata
    print("Fetching page metadata...")
    metadata = fetch_page_metadata(url)
    print(f"✓ Page title: {metadata['title']}")
    print(f"✓ Description: {metadata['description'][:100]}..." if metadata['description'] else "✓ No description found")
    print(f"✓ Featured image: {metadata['image_url']}" if metadata['image_url'] else "✓ No featured image found")
    
    try:
        # Initialize Bluesky client
        print("Connecting to Bluesky...")
        client = Client()
        client.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)
        print("✓ Successfully logged in to Bluesky")
        
        # Create and send the post with embed
        print("Creating post with embedded link...")
        response = create_post_with_embed(client, url, comment, metadata)
        
        if response:
            print("✓ Post created successfully!")
            print(f"Post URI: {response.uri}")
            
            # Update files only if post was successful
            if update_files(line_to_post, remaining_lines):
                print("✓ Process completed successfully")
            else:
                print("⚠️  Post was created but file update failed")
        else:
            print("❌ Failed to create post")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
