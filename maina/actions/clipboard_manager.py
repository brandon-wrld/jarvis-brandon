"""
clipboard_manager.py — Saves and recalls named text snippets ("clips"),
and can push a saved (or ad-hoc) snippet straight onto the OS clipboard.

Snippets persist in memory/clipboard_snippets.json so they survive restarts.
"""

import json
import sys
from pathlib import Path

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _store_path() -> Path:
    p = _get_base_dir() / "memory" / "clipboard_snippets.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load() -> dict:
    path = _store_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict):
    _store_path().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def clipboard_manager(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    action = (params.get("action") or "").lower().strip()
    name = (params.get("name") or "").strip()
    text = params.get("text", "")

    if player:
        player.write_log(f"[clipboard_manager] {action} {name}")

    data = _load()

    if action == "save":
        if not name:
            return "No snippet name provided."
        source_text = text or (pyperclip.paste() if _PYPERCLIP else "")
        if not source_text:
            return "No text provided and clipboard is empty."
        data[name] = source_text
        _save(data)
        return f"Saved snippet '{name}' ({len(source_text)} chars)."

    if action == "recall":
        if not name:
            return "No snippet name provided."
        if name not in data:
            return f"No snippet named '{name}'."
        if _PYPERCLIP:
            pyperclip.copy(data[name])
            return f"Snippet '{name}' copied to clipboard."
        return f"'{name}': {data[name]}"

    if action == "list":
        if not data:
            return "No saved snippets yet."
        return "Saved snippets: " + ", ".join(data.keys())

    if action == "delete":
        if name in data:
            del data[name]
            _save(data)
            return f"Deleted snippet '{name}'."
        return f"No snippet named '{name}'."

    return f"Unknown clipboard action: '{action}'. Use save, recall, list, or delete."
