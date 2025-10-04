import requests
import os
import spotipy
from auth import *
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope="user-library-read",
                                               cache_path="token.txt"))

def get_all_playlists():
    playlists = []
    limit = 50
    offset = 0
    playlists = sp.current_user_playlists(limit, offset)
    return playlists

## https://stackoverflow.com/questions/39086287/spotipy-how-to-read-more-than-100-tracks-from-a-playlist
def get_playlist_tracks(username,playlist_id):
    results = sp.user_playlist_tracks(username,playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

def save_playlists_to_files(this_list, listname):
    if not os.path.exists('lists'):
        os.makedirs('lists')
    # Sanitize filename for filesystem
    safe_name = listname.replace('/', '_').replace('\\', '_')
    filename = f"lists/{safe_name}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
         f.write(f"Playlist: {listname}\n")
         f.write("Tracks:\n")
            # Optionally, you can fetch and list track names here
         for eachtrack in this_list:
             f.write(f"{eachtrack}\n")

# Example usage (replace 'your_access_token_here' with your actual token)
playlists = get_all_playlists()
#print(playlists)
for each in playlists['items']:
   this_list=[]
   #print(each['name'])
   listid = each['id']
   ownerid = each['owner']['id']
   #print("\n")
   mytracks = get_playlist_tracks(ownerid,listid)
   for eachtrack in mytracks:
      trackentry = f"{eachtrack['track']['artists'][0]['name']} - {eachtrack['track']['album']['name']} - {eachtrack['track']['name']}"
      this_list.append(trackentry)
      #print(trackentry)
   save_playlists_to_files(this_list, each['name'])
