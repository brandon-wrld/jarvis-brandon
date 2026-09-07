"""
email_draft.py — Opens Gmail (or the OS default mail client) with a new
message pre-filled with recipient, subject, and body.

Two strategies, tried in order:
  1. Gmail web compose via a "mailto"-style deep URL — no login flow
     needed beyond an already-signed-in browser profile.
  2. 'mailto:' link, which hands off to whatever mail client/webmail
     the OS has registered as default.
"""

import platform
import subprocess
import webbrowser
from urllib.parse import quote

_SYSTEM = platform.system()


def _gmail_compose_url(to: str, subject: str, body: str) -> str:
    return (
        "https://mail.google.com/mail/?view=cm&fs=1"
        f"&to={quote(to)}&su={quote(subject)}&body={quote(body)}"
    )


def _mailto_url(to: str, subject: str, body: str) -> str:
    return f"mailto:{quote(to)}?subject={quote(subject)}&body={quote(body)}"


def email_draft(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    to = params.get("to", "").strip()
    subject = params.get("subject", "").strip()
    body = params.get("body", "").strip()
    use_gmail = params.get("use_gmail", True)

    if player:
        player.write_log(f"[email_draft] to={to} subject={subject[:40]}")

    try:
        if use_gmail:
            url = _gmail_compose_url(to, subject, body)
            webbrowser.open(url)
            return f"Opened a Gmail draft to {to or '(no recipient)'} with subject '{subject}'."

        url = _mailto_url(to, subject, body)
        if _SYSTEM == "Darwin":
            subprocess.run(["open", url])
        elif _SYSTEM == "Windows":
            subprocess.run(["start", "", url], shell=True)
        else:
            subprocess.run(["xdg-open", url])
        return f"Opened your default mail client with a draft to {to or '(no recipient)'}."
    except Exception as e:
        return f"Failed to open email draft: {e}"
