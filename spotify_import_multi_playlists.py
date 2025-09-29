#!/usr/bin/env python3
"""
Create multiple Spotify playlists from CSV files (tracks).

Each CSV must contain columns:
- Track Name
- Artist Name(s)   (multiple artists separated by ';')
- Album Name

Default behavior: for each CSV file, create a playlist named after the filename
without extension. Example: "playlist_日文_final.csv" -> playlist "playlist_日文_final".

Usage:
  export SPOTIFY_OAUTH="Bearer YOUR_OAUTH_TOKEN"
  export SPOTIFY_USER_ID="your_spotify_user_id"
  python spotify_import_multi_playlists.py playlist_中文_final.csv playlist_日文_final.csv

Options:
  --public            Create playlists as public (default: private)
  --private           Create playlists as private (default)
  --dry-run           Do not create or modify playlists; just print.
  --playlist-prefix   Prefix to add to all created playlist names (e.g., "Lang | ")
  --playlist-suffix   Suffix to add to all created playlist names (e.g., " (2025)")
  --token             OAuth token with 'Bearer ' prefix (otherwise use env SPOTIFY_OAUTH)
  --user              Spotify user id (otherwise use env SPOTIFY_USER_ID)
  --description       Description to set on created playlists (applies to all)
"""

import argparse
import csv
import json
import os
import sys
import time
import unicodedata
from typing import List, Dict, Optional
import requests
from pathlib import Path

SEARCH_ENDPOINT = "https://api.spotify.com/v1/search"
CREATE_PLAYLIST_ENDPOINT = "https://api.spotify.com/v1/users/{user_id}/playlists"
PLAYLIST_ITEMS_ENDPOINT = "https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
GET_ME_ENDPOINT = "https://api.spotify.com/v1/me"
GET_PLAYLISTS_ENDPOINT = "https://api.spotify.com/v1/me/playlists"

def norm(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", s).lower().strip()
    for ch in ['“','”','‘','’','–','—','‐','‑','‒']:
        s = s.replace(ch, ' ')
    import re
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def split_artists(artists_field: str) -> List[str]:
    if not artists_field:
        return []
    return [a.strip() for a in artists_field.split(";") if a.strip()]

def handle_rate(resp: requests.Response) -> bool:
    """Return True if caller should retry (handled 429), else False."""
    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", "1"))
        time.sleep(retry_after + 1)
        return True
    return False

def search_track(session: requests.Session, token: str, title: str, artists: List[str], album: str) -> Optional[str]:
    headers = {"Authorization": token}
    queries = []
    main_artist = artists[0] if artists else ""
    if album:
        queries.append(f'track:"{title}" artist:"{main_artist}" album:"{album}"')
    if main_artist:
        queries.append(f'track:"{title}" artist:"{main_artist}"')
    queries.append(f'track:"{title}"')

    target_title = norm(title)
    target_album = norm(album)
    target_artists = {norm(a) for a in artists}

    for q in queries:
        params = {"q": q, "type": "track", "limit": 10}
        resp = session.get(SEARCH_ENDPOINT, headers=headers, params=params)
        if handle_rate(resp):
            resp = session.get(SEARCH_ENDPOINT, headers=headers, params=params)
        if not resp.ok:
            continue
        items = resp.json().get("tracks", {}).get("items", [])‵
        best_uri, best_score = None, -1
        for it in items:
            it_title = norm(it.get("name",""))
            it_album = norm((it.get("album") or {}).get("name",""))
            it_artists = {norm(a.get("name","")) for a in (it.get("artists") or [])}
            score = 0
            if it_title == target_title:
                score += 3
            elif target_title and target_title in it_title:
                score += 2
            if target_artists & it_artists:
                score += 3
            if target_album and (it_album == target_album or target_album in it_album):
                score += 1
            for a in target_artists:
                if a and any(a in x for x in it_artists):
                    score += 1
            if score > best_score:
                best_score = score
                best_uri = it.get("uri")
        if best_uri:
            return best_uri
    return None

def add_tracks(session: requests.Session, token: str, playlist_id: str, uris: List[str], dry_run: bool=False) -> None:
    if dry_run or not uris:
        return
    headers = {"Authorization": token, "Content-Type": "application/json"}
    url = PLAYLIST_ITEMS_ENDPOINT.format(playlist_id=playlist_id)
    for i in range(0, len(uris), 100):
        chunk = uris[i:i+100]
        body = {"uris": chunk}
        while True:
            resp = session.post(url, headers=headers, data=json.dumps(body))
            if handle_rate(resp):
                continue
            if not resp.ok:
                print(f"[ERROR] Add chunk failed {resp.status_code}: {resp.text}", file=sys.stderr)
            break

def read_csv_rows(path: str) -> List[Dict[str,str]]:
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def ensure_user_id(session: requests.Session, token: str, user_id: Optional[str]) -> str:
    if user_id:
        return user_id
    headers = {"Authorization": token}
    resp = session.get(GET_ME_ENDPOINT, headers=headers)
    if handle_rate(resp):
        resp = session.get(GET_ME_ENDPOINT, headers=headers)
    resp.raise_for_status()
    return resp.json().get("id")

def find_existing_playlist(session: requests.Session, token: str, name: str) -> Optional[str]:
    headers = {"Authorization": token}
    url = GET_PLAYLISTS_ENDPOINT
    params = {"limit": 50}
    while True:
        resp = session.get(url, headers=headers, params=params)
        if handle_rate(resp):
            continue
        if not resp.ok:
            break
        data = resp.json()
        for pl in data.get("items", []):
            if pl.get("name") == name:
                return pl.get("id")
        if data.get("next"):
            url = data["next"]
            params = None
        else:
            break
    return None

def create_playlist(session: requests.Session, token: str, user_id: str, name: str, public: bool, description: str, dry_run: bool) -> str:
    if dry_run:
        print(f"[DRY] Would create (or reuse) playlist: {name}")
        return "DRY_PLAYLIST_ID"
    # Reuse if exists
    exist = find_existing_playlist(session, token, name)
    if exist:
        print(f"[OK ] Reusing existing playlist: {name} ({exist})")
        return exist
    headers = {"Authorization": token, "Content-Type": "application/json"}
    url = CREATE_PLAYLIST_ENDPOINT.format(user_id=user_id)
    body = {"name": name, "public": public, "description": description[:300] if description else ""}
    resp = session.post(url, headers=headers, data=json.dumps(body))
    if handle_rate(resp):
        resp = session.post(url, headers=headers, data=json.dumps(body))
    resp.raise_for_status()
    pid = resp.json().get("id")
    print(f"[OK ] Created playlist: {name} ({pid})")
    return pid

def infer_playlist_name(path: str, prefix: str, suffix: str) -> str:
    base = Path(path).stem  # filename without extension
    return f"{prefix}{base}{suffix}"

def process_csv(session: requests.Session, token: str, playlist_id: str, csv_path: str, dry_run: bool=False) -> int:
    rows = read_csv_rows(csv_path)
    uris = []
    added = 0
    for row in rows:
        title = row.get("Track Name") or row.get("Title") or ""
        artists_field = row.get("Artist Name(s)") or row.get("Artist") or ""
        album = row.get("Album Name") or row.get("Album") or ""
        artists = split_artists(artists_field)
        uri = search_track(session, token, title, artists, album)
        if uri:
            uris.append(uri)
            added += 1
            print(f"[FOUND] {title} — {artists_field}")
        else:
            print(f"[MISS ] {title} — {artists_field}")
    add_tracks(session, token, playlist_id, uris, dry_run=dry_run)
    print(f"[DONE] {csv_path}: matched {added}/{len(rows)}")
    return added

def main():
    ap = argparse.ArgumentParser(description="Create multiple Spotify playlists from CSV files.")
    ap.add_argument("csv", nargs="+", help="CSV files (Track Name, Artist Name(s), Album Name)")
    ap.add_argument("--public", action="store_true", help="Create as public (default private)")
    ap.add_argument("--private", action="store_true", help="Create as private (default)")
    ap.add_argument("--dry-run", action="store_true", help="Do not create/add, only print")
    ap.add_argument("--playlist-prefix", default="", help="Prefix for playlist names")
    ap.add_argument("--playlist-suffix", default="", help="Suffix for playlist names")
    ap.add_argument("--token", help="OAuth token with 'Bearer ' prefix (or env SPOTIFY_OAUTH)")
    ap.add_argument("--user", help="Spotify user id (or env SPOTIFY_USER_ID)")
    ap.add_argument("--description", default="Imported via CSV", help="Playlist description")
    args = ap.parse_args()

    token = args.token or os.getenv("SPOTIFY_OAUTH")
    if not token or not token.lower().startswith("bearer "):
        print("ERROR: Provide OAuth token with 'Bearer ' prefix via --token or SPOTIFY_OAUTH env.", file=sys.stderr)
        sys.exit(1)

    session = requests.Session()
    user_id = ensure_user_id(session, token, args.user or os.getenv("SPOTIFY_USER_ID"))

    public = args.public and not args.private  # --public wins; default private
    created_total = 0
    for csv_path in args.csv:
        pname = infer_playlist_name(csv_path, args.playlist_prefix, args.playlist_suffix)
        pid = create_playlist(session, token, user_id, pname, public=public, description=args.description, dry_run=args.dry_run)
        if pid != "DRY_PLAYLIST_ID":
            created_total += 1
        process_csv(session, token, pid, csv_path, dry_run=args.dry_run)

    print(f"\nAll done. Processed {len(args.csv)} CSV files; created/reused {created_total} playlists.")

if __name__ == "__main__":
    main()
