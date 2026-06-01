#!/usr/bin/env python3
"""
maloja_weekly_backfill.py
Generates weekly music listening digests for every week from Feb 2005 to today.
Skips weeks with no scrobbles. Saves markdown files to the archive folder.

Run once manually to backfill history.
"""

import requests
import os
from datetime import date, datetime, timedelta

# ─── CONFIG ───────────────────────────────────────────────────────────────────
MALOJA_URL = "https://maloja.lameazoid.com"   # No trailing slash
ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")
TOP_N = 5
BACKFILL_START = date(2005, 2, 1)
# ──────────────────────────────────────────────────────────────────────────────


def maloja_get(endpoint, params=None):
    """Make a GET request to the Maloja API."""
    url = f"{MALOJA_URL}/apis/mlj_1/{endpoint}"
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"[error] Failed to fetch {endpoint}: {e}")
        return None


def build_digest(since_date_api, since_str, today_str):
    """Fetch data from Maloja for a specific week and build markdown content.
    Returns None if there are no scrobbles for the period."""

    all_scrobbles = maloja_get("scrobbles", {"since": since_date_api, "to": today_str.replace("-", "/"), "max": 10000})

    # Skip weeks with no data
    if not all_scrobbles or "list" not in all_scrobbles or len(all_scrobbles["list"]) == 0:
        return None

    top_artists = maloja_get("charts/artists", {"since": since_date_api, "to": today_str.replace("-", "/"), "max": TOP_N})
    top_tracks  = maloja_get("charts/tracks",  {"since": since_date_api, "to": today_str.replace("-", "/"), "max": TOP_N})
    top_albums  = maloja_get("charts/albums",  {"since": since_date_api, "to": today_str.replace("-", "/"), "max": TOP_N})

    lines = []
    lines.append(f"# Music Listening: {since_str} to {today_str}\n")
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
            title = album.get("albumtitle", album.get("name", "Unknown")) if isinstance(album, dict) else str(album)
            artists = album.get("artists", []) if isinstance(album, dict) else []
            artist_str = ", ".join(artists) if artists else "Unknown Artist"
            count = entry.get("scrobbles", "?")
            lines.append(f"{i}. **{title}** by {artist_str} — {count} scrobbles")
    else:
        lines.append("*No data available.*")

    # ── All Scrobbles ──
    lines.append("\n## All Scrobbles This Week\n")
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

    return "\n".join(lines)


def note_title(today_str):
    """Returns the standard title format using the week end date."""
    d = datetime.strptime(today_str, "%Y-%m-%d")
    return d.strftime("%Y.%m.%d") + " - Weekly Music Listening"


def save_to_file(content, today_str):
    """Save markdown content to the archive folder."""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    filename = f"{note_title(today_str)}.md"
    filepath = os.path.join(ARCHIVE_DIR, filename)
    # Don't overwrite existing files
    if os.path.exists(filepath):
        print(f"[skip] Already exists: {filename}")
        return None
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[saved] {filename}")
    return filepath


def main():
    today = date.today()
    current_end = today
    weeks_processed = 0
    weeks_skipped = 0

    print(f"[backfill] Starting from {today} back to {BACKFILL_START}")
    print(f"[backfill] Saving to {ARCHIVE_DIR}\n")

    while current_end > BACKFILL_START:
        current_start = current_end - timedelta(days=7)
        if current_start < BACKFILL_START:
            current_start = BACKFILL_START

        since_date_api = current_start.strftime("%Y/%m/%d")
        since_str = current_start.strftime("%Y-%m-%d")
        today_str = current_end.strftime("%Y-%m-%d")

        content = build_digest(since_date_api, since_str, today_str)

        if content is None:
            weeks_skipped += 1
        else:
            save_to_file(content, today_str)
            weeks_processed += 1

        current_end -= timedelta(days=7)

    print(f"\n[backfill] Done. {weeks_processed} weeks saved, {weeks_skipped} weeks skipped (no scrobbles).")


if __name__ == "__main__":
    main()
