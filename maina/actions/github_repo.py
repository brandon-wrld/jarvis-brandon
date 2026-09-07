"""
github_repo.py — Creates a new GitHub repository for the user.

Requires a GitHub Personal Access Token (classic or fine-grained, with
'repo' scope) saved in config/api_keys.json as "github_token".

Pattern matches the rest of the actions/ package:
    def github_repo(parameters=None, response=None, player=None, session_memory=None) -> str
"""

import json
import sys
import webbrowser
from pathlib import Path

try:
    import requests
    _REQUESTS = True
except ImportError:
    _REQUESTS = False


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _get_token() -> str:
    cfg_path = _get_base_dir() / "config" / "api_keys.json"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("github_token", "")


def github_repo(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    name = (params.get("name") or "").strip()
    description = params.get("description", "")
    private = bool(params.get("private", False))

    if not name:
        return "No repository name provided."

    if player:
        player.write_log(f"[github_repo] {name}")

    if not _REQUESTS:
        return "The 'requests' package is required for github_repo. Run: pip install requests"

    token = _get_token()
    if not token:
        # Fall back to opening the "create repo" page pre-filled, so the
        # user can still finish the action manually without a token.
        url = f"https://github.com/new?name={name.replace(' ', '-')}&description={description}"
        webbrowser.open(url)
        return (
            "No GitHub token configured, so I opened the repository "
            "creation page in your browser instead."
        )

    try:
        resp = requests.post(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={
                "name": name,
                "description": description,
                "private": private,
            },
            timeout=15,
        )
        if resp.status_code == 201:
            html_url = resp.json().get("html_url", "")
            return f"Repository '{name}' created: {html_url}"
        return f"GitHub API error ({resp.status_code}): {resp.text[:200]}"
    except Exception as e:
        return f"Failed to create repository: {e}"
