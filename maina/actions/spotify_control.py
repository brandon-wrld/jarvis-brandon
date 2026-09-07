"""
spotify_control.py — Controls Spotify playback: play a track/playlist/artist
by name, pause, skip, adjust volume.

Uses the Spotify Web API via 'spotipy'. Requires a one-time OAuth login;
credentials come from config/api_keys.json:

    "spotify_client_id":     "...",
    "spotify_client_secret": "...",
    "spotify_redirect_uri":  "http://127.0.0.1:8080/callback"

Falls back to simply launching the Spotify app (via actions.open_app) if
spotipy or credentials aren't available, so the skill degrades gracefully.
"""

import json
import sys
from pathlib import Path

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    _SPOTIPY = True
except ImportError:
    _SPOTIPY = False

from actions.open_app import open_app

_SCOPE = "user-modify-playback-state user-read-playback-state"
_client = None


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _get_creds() -> dict:
    cfg_path = _get_base_dir() / "config" / "api_keys.json"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_client():
    global _client
    if _client is not None:
        return _client
    creds = _get_creds()
    cid = creds.get("spotify_client_id")
    secret = creds.get("spotify_client_secret")
    redirect = creds.get("spotify_redirect_uri", "http://127.0.0.1:8080/callback")
    if not (cid and secret):
        return None
    _client = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=cid,
        client_secret=secret,
        redirect_uri=redirect,
        scope=_SCOPE,
        open_browser=True,
    ))
    return _client


def _find_active_device(sp) -> str | None:
    devices = sp.devices().get("devices", [])
    if not devices:
        return None
    active = next((d for d in devices if d.get("is_active")), devices[0])
    return active["id"]


def spotify_control(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    action = (params.get("action") or "play").lower().strip()
    query = params.get("query", "").strip()

    if player:
        player.write_log(f"[spotify_control] {action} {query}")

    if not _SPOTIPY:
        open_app(parameters={"app_name": "spotify"}, player=player)
        return "spotipy isn't installed (pip install spotipy), so I just opened the Spotify app instead."

    sp = _get_client()
    if sp is None:
        open_app(parameters={"app_name": "spotify"}, player=player)
        return "No Spotify API credentials configured, so I just opened the Spotify app instead."

    # Ensure the desktop app / a device is up so we have somewhere to play to.
    open_app(parameters={"app_name": "spotify"}, player=player)

    try:
        device_id = _find_active_device(sp)

        if action in ("play", "playlist", "song", "track"):
            if not query:
                sp.start_playback(device_id=device_id)
                return "Resumed playback."

            search_type = "playlist" if "playlist" in action else "track"
            results = sp.search(q=query, type=search_type, limit=1)
            items = results.get(f"{search_type}s", {}).get("items", [])
            if not items:
                # try the other type as a fallback
                other = "track" if search_type == "playlist" else "playlist"
                results = sp.search(q=query, type=other, limit=1)
                items = results.get(f"{other}s", {}).get("items", [])
                search_type = other
            if not items:
                return f"Couldn't find '{query}' on Spotify."

            uri = items[0]["uri"]
            name = items[0]["name"]
            if search_type == "playlist":
                sp.start_playback(device_id=device_id, context_uri=uri)
            else:
                sp.start_playback(device_id=device_id, uris=[uri])
            return f"Playing {search_type}: {name}"

        if action == "pause":
            sp.pause_playback(device_id=device_id)
            return "Paused."

        if action in ("next", "skip"):
            sp.next_track(device_id=device_id)
            return "Skipped to next track."

        if action in ("previous", "back"):
            sp.previous_track(device_id=device_id)
            return "Went back a track."

        if action == "volume":
            level = int(params.get("level", 50))
            sp.volume(level, device_id=device_id)
            return f"Volume set to {level}%."

        return f"Unknown spotify action: '{action}'"

    except Exception as e:
        return f"Spotify control error: {e}"
