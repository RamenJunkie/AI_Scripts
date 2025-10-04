# YouTube Playlist Creator

A Python script that automatically creates YouTube playlists from text files. Simply list your songs or search queries in a text file, and the script will search for them and add them to a playlist.

## Features

- 🎵 Creates playlists from simple text files
- 🔍 Searches YouTube for each line in your file
- ♻️ Appends to existing playlists if they already exist
- 🚫 Automatically skips duplicate videos
- 📊 Provides detailed progress and summary statistics
- 💾 Quota-aware (shows what failed vs succeeded)

## Prerequisites

- Python 3.7 or higher
- A Google Cloud project with YouTube Data API v3 enabled
- OAuth 2.0 credentials from Google Cloud Console

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get YouTube API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **YouTube Data API v3**:
   - Go to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the credentials and save as `client_secret.json` in the same directory as the script

### 3. Create Your Song List

Create a text file with one search query per line. The filename (without extension) will be used as the playlist name.

**Example: `my_favorites.txt`**
```
Artist Name - Song Title
Another Artist - Another Song
Just a Song Name
Band Name Song Name
```

Each line will be searched on YouTube exactly as written, and the first result will be added to the playlist.

## Usage

```bash
python main.py <input_file>
```

**Example:**
```bash
python main.py my_favorites.txt
```

This will:
1. Search for a playlist named "my_favorites"
2. Create it if it doesn't exist, or use the existing one
3. Search YouTube for each line in the file
4. Add videos to the playlist (skipping any duplicates)

### First Run

On the first run, a browser window will open asking you to:
1. Sign in to your Google account
2. Grant the script permission to manage your YouTube playlists

The credentials will be cached for future runs.

## Output

The script provides detailed feedback:

```
Found existing playlist: my_favorites
Checking for existing videos in playlist...
Found 10 existing videos

Searching for: Artist - Song
  ✓ Added to playlist
Searching for: Another Artist - Song
  ⏭️  Already in playlist, skipping
Searching for: Unknown Song XYZ
  ❌ No results found

==================================================
Done! Playlist ID: PLxxxxxxxxxxxxx
Successfully added: 15
Skipped (already in playlist): 5
Failed: 2
==================================================
```

## Quota Limits

The YouTube Data API has daily quota limits:

- **Default quota**: 10,000 units per day
- **Cost per song**: ~150 units (100 for search + 50 for adding to playlist)
- **Maximum songs per day**: ~66 songs

The quota resets at midnight Pacific Time (PT).

### Tips to Stay Within Quota

1. Split large playlists across multiple days
2. Re-running the script is efficient (duplicates only cost search quota, not insertion)
3. Request a quota increase from Google Cloud Console if needed
4. Check your usage at: Google Cloud Console → APIs & Services → YouTube Data API v3 → Quotas

## Troubleshooting

### "Quota exceeded" error
You've hit the daily API limit. Wait until midnight PT for the quota to reset, or request a quota increase.

### "Invalid credentials" error
Delete any cached credential files and run the script again to re-authenticate.

### "No results found" for a song
Try reformatting the search query in your text file. More specific queries usually work better (include artist name).

### Videos aren't being added
Check that your OAuth credentials have the correct scope (`youtube.force-ssl`) and that you've granted permission to manage your playlists.

## File Structure

```
.
├── main.py              # The main script
├── client_secret.json   # Your OAuth credentials (not included)
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── *.txt               # Your song list files
```

## Privacy

- Playlists are created as **private** by default
- The script only accesses your YouTube account (no data is sent elsewhere)
- Your credentials are stored locally

## License

This project is provided as-is for personal use.
