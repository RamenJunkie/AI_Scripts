import os
import argparse
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def authenticate_youtube():
    """Authenticate and return YouTube service object."""
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    credentials = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=credentials)


def find_playlist_by_name(youtube, playlist_name):
    """Search for an existing playlist by name. Returns playlist ID if found, None otherwise."""
    try:
        playlists = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50
        ).execute()
        
        for playlist in playlists.get("items", []):
            if playlist["snippet"]["title"] == playlist_name:
                return playlist["id"]
        
        # Check if there are more pages
        next_page_token = playlists.get("nextPageToken")
        while next_page_token:
            playlists = youtube.playlists().list(
                part="snippet",
                mine=True,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            for playlist in playlists.get("items", []):
                if playlist["snippet"]["title"] == playlist_name:
                    return playlist["id"]
            
            next_page_token = playlists.get("nextPageToken")
        
        return None
    except Exception as e:
        print(f"Error searching for playlists: {e}")
        return None


def create_playlist(youtube, playlist_name):
    """Create a new YouTube playlist and return its ID."""
    playlist = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": playlist_name,
                "description": f"Auto-generated from {playlist_name}"
            },
            "status": {"privacyStatus": "private"}
        }
    ).execute()
    
    print(f"Created new playlist: {playlist_name}")
    return playlist["id"]


def get_existing_videos_in_playlist(youtube, playlist_id):
    """Get set of all video IDs already in the playlist."""
    video_ids = set()
    
    try:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50
        )
        
        while request:
            response = request.execute()
            
            for item in response.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                video_ids.add(video_id)
            
            request = youtube.playlistItems().list_next(request, response)
        
        return video_ids
    except Exception as e:
        print(f"Error getting existing videos: {e}")
        return set()


def get_or_create_playlist(youtube, playlist_name):
    """Get existing playlist by name, or create a new one if it doesn't exist."""
    playlist_id = find_playlist_by_name(youtube, playlist_name)
    
    if playlist_id:
        print(f"Found existing playlist: {playlist_name}")
        return playlist_id
    else:
        return create_playlist(youtube, playlist_name)


def search_video(youtube, query):
    """Search for a video and return the video ID of the first result."""
    search_response = youtube.search().list(
        q=query,
        part="id",
        maxResults=1,
        type="video"
    ).execute()
    
    items = search_response.get("items", [])
    return items[0]["id"]["videoId"] if items else None


def add_video_to_playlist(youtube, playlist_id, video_id):
    """Add a video to the specified playlist."""
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    ).execute()


def create_playlist_and_add_songs(file_path):
    """Main function to create playlist and add songs from file."""
    # Authenticate
    youtube = authenticate_youtube()
    
    # Get playlist name from filename
    playlist_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Get or create playlist
    playlist_id = get_or_create_playlist(youtube, playlist_name)
    
    # Get existing videos to avoid duplicates
    print("Checking for existing videos in playlist...")
    existing_videos = get_existing_videos_in_playlist(youtube, playlist_id)
    print(f"Found {len(existing_videos)} existing videos\n")
    
    # Process each line from the file
    added_count = 0
    skipped_count = 0
    failed_count = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            query = line.strip()
            
            # Skip empty lines
            if not query:
                continue
            
            print(f"Searching for: {query}")
            
            # Search for video
            video_id = search_video(youtube, query)
            
            if not video_id:
                print(f"  ❌ No results found")
                failed_count += 1
                continue
            
            # Check if video already exists in playlist
            if video_id in existing_videos:
                print(f"  ⏭️  Already in playlist, skipping")
                skipped_count += 1
                continue
            
            # Add to playlist
            try:
                add_video_to_playlist(youtube, playlist_id, video_id)
                print(f"  ✓ Added to playlist")
                added_count += 1
                existing_videos.add(video_id)  # Update our cache
            except Exception as e:
                print(f"  ❌ Error adding to playlist: {e}")
                failed_count += 1
    
    print(f"\n{'='*50}")
    print(f"Done! Playlist ID: {playlist_id}")
    print(f"Successfully added: {added_count}")
    print(f"Skipped (already in playlist): {skipped_count}")
    print(f"Failed: {failed_count}")
    print(f"{'='*50}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a YouTube playlist from a text file with search queries"
    )
    parser.add_argument("input_file", help="Text file with one search query per line")
    args = parser.parse_args()
    
    create_playlist_and_add_songs(args.input_file)
