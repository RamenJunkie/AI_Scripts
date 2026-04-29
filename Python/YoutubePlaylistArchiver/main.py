#!/usr/bin/env python3
"""
YouTube Playlist Backup Script
Backs up YouTube playlists to markdown files with video links.

Requirements:
    pip install google-api-python-client

Usage:
    python backup_playlist.py -p PLAYLIST_URL_OR_ID
    python backup_playlist.py -c CHANNEL_URL_OR_ID

Setup:
    1. Go to https://console.cloud.google.com/
    2. Create a new project or select existing
    3. Enable YouTube Data API v3
    4. Create credentials (API Key)
    5. Set environment variable: export YOUTUBE_API_KEY="your_api_key"
"""

import os
import sys
import re
import argparse
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def extract_playlist_id(url_or_id):
    """Extract playlist ID from URL or return ID if already provided."""
    # If it's already just an ID
    if len(url_or_id) == 34 and url_or_id.startswith('PL'):
        return url_or_id
    
    # Extract from various YouTube URL formats
    patterns = [
        r'list=([a-zA-Z0-9_-]+)',
        r'playlist\?list=([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    return url_or_id

def extract_channel_id(url_or_id):
    """Extract channel ID from URL or return ID/handle if already provided."""
    # Channel ID format: UC...
    if url_or_id.startswith('UC') and len(url_or_id) == 24:
        return url_or_id, 'id'
    
    # Handle format: @username
    if url_or_id.startswith('@'):
        return url_or_id, 'handle'
    
    # Extract from various YouTube URL formats
    patterns = [
        (r'youtube\.com/channel/(UC[a-zA-Z0-9_-]{22})', 'id'),
        (r'youtube\.com/@([a-zA-Z0-9_-]+)', 'handle'),
        (r'youtube\.com/c/([a-zA-Z0-9_-]+)', 'handle'),
        (r'youtube\.com/user/([a-zA-Z0-9_-]+)', 'handle'),
    ]
    
    for pattern, id_type in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            channel_identifier = match.group(1)
            if id_type == 'handle' and not channel_identifier.startswith('@'):
                channel_identifier = '@' + channel_identifier
            return channel_identifier, id_type
    
    # Default: assume it's a handle or username
    identifier = url_or_id if url_or_id.startswith('@') else '@' + url_or_id
    return identifier, 'handle'

def get_channel_id_from_handle(youtube, handle):
    """Convert channel handle to channel ID."""
    try:
        request = youtube.channels().list(
            part="id",
            forHandle=handle.lstrip('@')
        )
        response = request.execute()
        
        if response['items']:
            return response['items'][0]['id']
    except:
        pass
    
    # Try searching for the channel
    try:
        request = youtube.search().list(
            part="snippet",
            q=handle,
            type="channel",
            maxResults=1
        )
        response = request.execute()
        
        if response['items']:
            return response['items'][0]['snippet']['channelId']
    except:
        pass
    
    return None

def sanitize_filename(name):
    """Remove characters that aren't safe for filenames."""
    return re.sub(r'[<>:"/\\|?*]', '', name)

def get_playlist_info(youtube, playlist_id):
    """Fetch playlist metadata."""
    request = youtube.playlists().list(
        part="snippet",
        id=playlist_id
    )
    response = request.execute()
    
    if not response['items']:
        raise ValueError(f"Playlist not found: {playlist_id}")
    
    return response['items'][0]['snippet']

def get_channel_playlists(youtube, channel_id):
    """Fetch all playlists from a channel."""
    playlists = []
    next_page_token = None
    
    print("Fetching playlists (this may take a moment)...")
    
    while True:
        try:
            request = youtube.playlists().list(
                part="snippet,contentDetails",
                channelId=channel_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            if 'items' not in response:
                break
            
            for item in response['items']:
                playlists.append({
                    'id': item['id'],
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle'],
                    'video_count': item['contentDetails']['itemCount']
                })
            
            print(f"  Found {len(playlists)} playlists so far...")
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
        except HttpError as e:
            print(f"  Warning: Error fetching playlists page: {e}")
            break
    
    return playlists

def get_playlist_videos(youtube, playlist_id):
    """Fetch all videos from a playlist."""
    videos = []
    next_page_token = None
    
    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()
        
        for item in response['items']:
            snippet = item['snippet']
            # Skip deleted/private videos
            if snippet['title'] == 'Deleted video' or snippet['title'] == 'Private video':
                videos.append({
                    'channel': 'Unknown',
                    'title': snippet['title'],
                    'video_id': None
                })
            else:
                videos.append({
                    'channel': snippet['videoOwnerChannelTitle'] or snippet['channelTitle'],
                    'title': snippet['title'],
                    'video_id': snippet['resourceId']['videoId']
                })
        
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return videos

def create_markdown(playlist_info, videos, date_str):
    """Generate markdown content."""
    title = playlist_info['title']
    channel = playlist_info['channelTitle']
    description = playlist_info.get('description', '')
    
    md = f"# {title}\n\n"
    md += f"**Channel:** {channel}  \n"
    md += f"**Backup Date:** {date_str}  \n"
    md += f"**Total Videos:** {len(videos)}  \n\n"
    
    if description:
        md += f"**Description:**  \n{description}\n\n"
    
    md += "---\n\n"
    md += "## Videos\n\n"
    
    for i, video in enumerate(videos, 1):
        channel_name = video['channel']
        title = video['title']
        
        if video['video_id']:
            url = f"https://www.youtube.com/watch?v={video['video_id']}"
            md += f"{i}. {channel_name} - [{title}]({url})\n"
        else:
            md += f"{i}. {channel_name} - {title} (unavailable)\n"
    
    return md

def backup_playlist(youtube, playlist_id, output_dir='.'):
    """Backup a single playlist to markdown."""
    # Get playlist info
    playlist_info = get_playlist_info(youtube, playlist_id)
    
    # Get all videos
    videos = get_playlist_videos(youtube, playlist_id)
    
    # Generate filename
    date_str = datetime.now().strftime('%Y-%m-%d')
    channel = sanitize_filename(playlist_info['channelTitle'])
    title = sanitize_filename(playlist_info['title'])
    filename = f"{date_str} - {channel} - {title}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Create markdown
    markdown_content = create_markdown(playlist_info, videos, date_str)
    
    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return filename, len(videos)

def backup_channel_playlists(youtube, channel_input):
    """Backup all playlists from a channel."""
    # Extract channel identifier
    channel_identifier, id_type = extract_channel_id(channel_input)
    print(f"Channel identifier: {channel_identifier}")
    
    # Get channel ID if we have a handle
    if id_type == 'handle':
        print("Converting handle to channel ID...")
        channel_id = get_channel_id_from_handle(youtube, channel_identifier)
        if not channel_id:
            raise ValueError(f"Could not find channel for handle: {channel_identifier}")
    else:
        channel_id = channel_identifier
    
    print(f"Channel ID: {channel_id}")
    
    # Get all playlists from channel
    print("\nFetching channel playlists...")
    playlists = get_channel_playlists(youtube, channel_id)
    
    if not playlists:
        print("No playlists found for this channel")
        return
    
    print(f"Found {len(playlists)} playlists\n")
    
    # Create output directory
    date_str = datetime.now().strftime('%Y-%m-%d')
    channel_name = sanitize_filename(playlists[0]['channel'])
    output_dir = f"{date_str} - {channel_name} - Playlists"
    os.makedirs(output_dir, exist_ok=True)
    
    # Backup each playlist
    successful = 0
    for i, playlist in enumerate(playlists, 1):
        print(f"[{i}/{len(playlists)}] Backing up: {playlist['title']} ({playlist['video_count']} videos)")
        try:
            filename, video_count = backup_playlist(youtube, playlist['id'], output_dir)
            print(f"  ✓ Saved to: {filename}")
            successful += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n{'='*60}")
    print(f"Backup complete!")
    print(f"Successfully backed up {successful}/{len(playlists)} playlists")
    print(f"Files saved to: {output_dir}/")
    print(f"{'='*60}")

def main():
    parser = argparse.ArgumentParser(
        description='Backup YouTube playlists to markdown files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Backup a single playlist:
    python backup_playlist.py -p "https://www.youtube.com/playlist?list=PLxxx"
    python backup_playlist.py -p PLxxx
  
  Backup all playlists from a channel:
    python backup_playlist.py -c "https://www.youtube.com/@channelname"
    python backup_playlist.py -c @channelname
    python backup_playlist.py -c UCxxx
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-p', '--playlist', help='Playlist URL or ID')
    group.add_argument('-c', '--channel', help='Channel URL, ID, or handle')
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("Error: YOUTUBE_API_KEY environment variable not set")
        print("Set it with: export YOUTUBE_API_KEY='your_api_key'")
        sys.exit(1)
    
    try:
        # Initialize YouTube API
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        if args.playlist:
            # Single playlist backup
            playlist_id = extract_playlist_id(args.playlist)
            print(f"Fetching playlist: {playlist_id}\n")
            
            filename, video_count = backup_playlist(youtube, playlist_id)
            print(f"\n{'='*60}")
            print(f"Backup complete!")
            print(f"Found {video_count} videos")
            print(f"Saved to: {filename}")
            print(f"{'='*60}")
        
        elif args.channel:
            # Channel playlists backup
            backup_channel_playlists(youtube, args.channel)
        
    except HttpError as e:
        print(f"\nYouTube API error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
