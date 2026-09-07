"""
calendar_event.py — Creates a real calendar event (not just a reminder).

Primary path: Google Calendar API (requires OAuth credentials.json +
token stored via google-auth-oauthlib — same style credential flow
most people already use for Gmail).

Fallback path (no Google creds configured): generates a standalone
.ics file and opens it, which any OS will hand off to the default
calendar app to add the event.
"""

import sys
import subprocess
import platform
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    _GOOGLE = True
except ImportError:
    _GOOGLE = False

_SYSTEM = platform.system()
_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _get_google_creds():
    base = _get_base_dir() / "config"
    token_path = base / "calendar_token.json"
    client_secret_path = base / "google_client_secret.json"

    if not client_secret_path.exists():
        return None

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), _SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def _parse_datetime(date_str: str, time_str: str) -> datetime:
    return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")


def _create_google_event(title, date_str, time_str, duration_min, location, description) -> str:
    creds = _get_google_creds()
    if not creds:
        return ""

    start = _parse_datetime(date_str, time_str)
    end = start + timedelta(minutes=duration_min)

    service = build("calendar", "v3", credentials=creds)
    event = {
        "summary": title,
        "location": location,
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": "local"},
        "end": {"dateTime": end.isoformat(), "timeZone": "local"},
    }
    created = service.events().insert(calendarId="primary", body=event).execute()
    return created.get("htmlLink", "")


def _create_ics_fallback(title, date_str, time_str, duration_min, location, description) -> Path:
    start = _parse_datetime(date_str, time_str)
    end = start + timedelta(minutes=duration_min)
    fmt = "%Y%m%dT%H%M%S"

    ics = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//JARVIS//Calendar Event//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uuid4()}@jarvis\r\n"
        f"DTSTART:{start.strftime(fmt)}\r\n"
        f"DTEND:{end.strftime(fmt)}\r\n"
        f"SUMMARY:{title}\r\n"
        f"LOCATION:{location}\r\n"
        f"DESCRIPTION:{description}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )

    out_path = Path.home() / "Desktop" / f"{title.replace(' ', '_')}.ics"
    out_path.write_text(ics, encoding="utf-8")
    return out_path


def _open_file(path: Path):
    try:
        if _SYSTEM == "Windows":
            subprocess.run(["start", "", str(path)], shell=True)
        elif _SYSTEM == "Darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])
    except Exception:
        pass


def calendar_event(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    title = params.get("title", "Untitled Event").strip()
    date_str = params.get("date", "")       # YYYY-MM-DD
    time_str = params.get("time", "09:00")  # HH:MM
    duration_min = int(params.get("duration_minutes", 60))
    location = params.get("location", "")
    description = params.get("description", "")

    if not date_str:
        return "No date provided for the event."

    if player:
        player.write_log(f"[calendar_event] {title} @ {date_str} {time_str}")

    if _GOOGLE:
        try:
            link = _create_google_event(title, date_str, time_str, duration_min, location, description)
            if link:
                return f"Event '{title}' created on {date_str} at {time_str}: {link}"
        except Exception as e:
            print(f"[calendar_event] Google Calendar failed, falling back to .ics: {e}")

    try:
        ics_path = _create_ics_fallback(title, date_str, time_str, duration_min, location, description)
        _open_file(ics_path)
        return (
            f"Google Calendar isn't configured, so I created an event file "
            f"and opened it for you to confirm: {ics_path}"
        )
    except Exception as e:
        return f"Failed to create event: {e}"
