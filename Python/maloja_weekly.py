#!/usr/bin/env python3
"""
maloja_weekly.py
Generates a weekly music listening digest from a Maloja server.
Saves a markdown file locally and creates a Joplin note.

Cron: 0 12 * * 6  (Saturday at noon)
"""

import requests
import subprocess
import os
import sys
from datetime import datetime, timedelta

# ─── CONFIG ───────────────────────────────────────────────────────────────────
MALOJA_URL = "https://your-maloja-instance.example.com"   # No trailing slash
JOPLIN_NOTEBOOK = "Music Listening"                        # Target notebook name
ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")
TOP_N = 5
# ──────────────────────────────────────────────────────────────────────────────


def get_week_range():
    """Returns (start, end) as YYYY-MM-DD strings for the previous week (Sun-Sat)."""
    today = datetime.now().date()
    # End = yesterday (Friday), Start = 6 days before that (Saturday prior)
    end = today - timedelta(days=1)
    start = end - timedelta(days=6)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def maloja_get(endpoint, params=None):
    """Make a GET request to the Maloja API."""
    url = f"{MALOJA_URL}/apis/maloja/{endpoint}"
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"[error] Failed to fetch {endpoint}: {e}")
        return None


def build_digest(start, end):
    """Fetch data from Maloja and build markdown content."""
    date_range = f"{start}/{end}"

    top_artists = maloja_get("charts/artists", {"range": date_range, "limit": TOP_N})
    top_tracks  = maloja_get("charts/tracks",  {"range": date_range, "limit": TOP_N})
    top_albums  = maloja_get("charts/albums",  {"range": date_range, "limit": TOP_N})
    all_scrobbles = maloja_get("scrobbles",    {"range": date_range, "limit": 10000})

    lines = []
    lines.append(f"# Music Listening: Week of {start} to {end}\n")
    lines.append(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    # ── Top Artists ──
    lines.append("\n## Top Artists\n")
    if top_artists and "list" in top_artists:
        for i, entry in enumerate(top_artists["list"][:TOP_N], 1):
            artist = entry.get("artist", {})
            name = artist.get("name", "Unknown") if isinstance(artist, dict) else str(artist)
            count = entry.get("scrobbles", "?")
            lines.append(f"{i}. **{name}** — {count} scrobbles")
    else:
        lines.append("*No data available.*")

    # ── Top Tracks ──
    lines.append("\n## Top Tracks\n")
    if top_tracks and "list" in top_tracks:
        for i, entry in enumerate(top_tracks["list"][:TOP_N], 1):
            track = entry.get("track", {})
            title = track.get("title", "Unknown") if isinstance(track, dict) else str(track)
            artists = track.get("artists", []) if isinstance(track, dict) else []
            artist_str = ", ".join(artists) if artists else "Unknown Artist"
            count = entry.get("scrobbles", "?")
            lines.append(f"{i}. **{title}** by {artist_str} — {count} scrobbles")
    else:
        lines.append("*No data available.*")

    # ── Top Albums ──
    lines.append("\n## Top Albums\n")
    if top_albums and "list" in top_albums:
        for i, entry in enumerate(top_albums["list"][:TOP_N], 1):
            album = entry.get("album", {})
            title = album.get("name", "Unknown") if isinstance(album, dict) else str(album)
            artists = album.get("artists", []) if isinstance(album, dict) else []
            artist_str = ", ".join(artists) if artists else "Unknown Artist"
            count = entry.get("scrobbles", "?")
            lines.append(f"{i}. **{title}** by {artist_str} — {count} scrobbles")
    else:
        lines.append("*No data available.*")

    # ── All Scrobbles ──
    lines.append("\n## All Scrobbles This Week\n")
    if all_scrobbles and "list" in all_scrobbles:
        total = len(all_scrobbles["list"])
        lines.append(f"*{total} total scrobbles*\n")
        lines.append("| Time | Artist | Track |")
        lines.append("|------|--------|-------|")
        for s in all_scrobbles["list"]:
            ts = s.get("time", 0)
            dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "?"
            track = s.get("track", {})
            title = track.get("title", "?") if isinstance(track, dict) else str(track)
            artists = track.get("artists", []) if isinstance(track, dict) else []
            artist_str = ", ".join(artists) if artists else "?"
            lines.append(f"| {dt} | {artist_str} | {title} |")
    else:
        lines.append("*No scrobble data available.*")

    return "\n".join(lines)


def note_title(end):
    """Returns the standard title format using the week end date."""
    d = datetime.strptime(end, "%Y-%m-%d")
    return d.strftime("%Y.%m.%d") + " - Weekly Music Listening"


def save_to_file(content, start, end):
    """Save markdown content to the archive folder."""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    filename = f"{note_title(end)}.md"
    filepath = os.path.join(ARCHIVE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[saved] {filepath}")
    return filepath


def save_to_joplin(content, start, end):
    """Create a note in Joplin via the CLI."""
    title = note_title(end)
    try:
        # Use the notebook
        subprocess.run(["joplin", "use", JOPLIN_NOTEBOOK], check=True, capture_output=True)
        # Create the note
        result = subprocess.run(
            ["joplin", "mknote", title],
            check=True, capture_output=True, text=True
        )
        print(f"[joplin] Created note: {title}")

        # Set the note body — pipe content via stdin to 'joplin set <note> body'
        subprocess.run(
            ["joplin", "set", title, "body", content],
            check=True, capture_output=True
        )
        print(f"[joplin] Note body set.")
    except subprocess.CalledProcessError as e:
        print(f"[error] Joplin CLI failed: {e}")
        print("        Is Joplin CLI running and configured?")


def main():
    start, end = get_week_range()
    print(f"[maloja_weekly] Generating digest for {start} to {end}")

    content = build_digest(start, end)
    save_to_file(content, start, end)
    save_to_joplin(content, start, end)

    print("[maloja_weekly] Done.")


if __name__ == "__main__":
    main()
