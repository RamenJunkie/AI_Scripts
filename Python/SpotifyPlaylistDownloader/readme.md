Spotify Playlist Exporter

A Python script that exports all your Spotify playlists to text files, with each track listed in a readable format.
Description

This tool connects to your Spotify account and saves all your playlists as individual text files. Each playlist is exported with full track information including artist name, album name, and track name.
Features

    Exports all playlists from your Spotify account
    Handles playlists with more than 100 tracks
    Saves each playlist as a separate text file
    Sanitizes filenames to ensure filesystem compatibility
    Creates organized output in a lists directory

Prerequisites

    Python 3.x
    A Spotify Developer account
    Spotify API credentials (Client ID and Client Secret)

Setup

    Get Spotify API Credentials
        Go to the Spotify Developer Dashboard
        Create a new app
        Note your Client ID and Client Secret
        Add http://localhost:8888/callback (or your preferred URI) to the Redirect URIs in your app settings
    Create an auth.py file Create a file named auth.py in the same directory with your credentials:

python

   SPOTIPY_CLIENT_ID = 'your_client_id_here'
   SPOTIPY_CLIENT_SECRET = 'your_client_secret_here'
   SPOTIPY_REDIRECT_URI = 'http://localhost:8888/callback'

    Install dependencies

bash

   pip install -r requirements.txt

Usage

Run the script:
bash

python main.py

On first run, the script will open a browser window asking you to authorize the application. After authorization, you'll be redirected to a URL. Copy the entire URL and paste it back into the terminal.

The script will create a lists directory and save each playlist as a text file.
Output Format

Each playlist file contains:

Playlist: [Playlist Name]
Tracks:
Artist Name - Album Name - Track Name
Artist Name - Album Name - Track Name
...

Files Generated

    lists/ - Directory containing all exported playlist files
    token.txt - OAuth token cache (automatically generated)

Notes

    The script only reads your library data; it does not modify your playlists
    Authentication tokens are cached locally in token.txt for convenience
    Playlist names with special characters (like / or \) are automatically sanitized for filenames

Acknowledgments

    Uses the Spotipy library for Spotify API integration
    Playlist pagination technique from Stack Overflow



