"""
notes.py — Appends timestamped entries to a running plain-text notes file
(one file per named notebook, default "general"), and can read them back.
"""

from datetime import datetime
from pathlib import Path

_NOTES_DIR = Path.home() / "Documents" / "Jarvis Notes"


def _notebook_path(notebook: str) -> Path:
    _NOTES_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in notebook if c.isalnum() or c in (" ", "_", "-")).strip() or "general"
    return _NOTES_DIR / f"{safe_name}.txt"


def notes(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    action = (params.get("action") or "append").lower().strip()
    notebook = params.get("notebook", "general")
    text = params.get("text", "").strip()

    if player:
        player.write_log(f"[notes] {action} -> {notebook}")

    path = _notebook_path(notebook)

    if action == "append":
        if not text:
            return "No note text provided."
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")
        return f"Added to '{notebook}' notes."

    if action == "read":
        if not path.exists():
            return f"Notebook '{notebook}' is empty."
        content = path.read_text(encoding="utf-8").strip()
        return content or f"Notebook '{notebook}' is empty."

    if action == "clear":
        if path.exists():
            path.unlink()
        return f"Cleared notebook '{notebook}'."

    if action == "list":
        if not _NOTES_DIR.exists():
            return "No notebooks yet."
        books = [p.stem for p in _NOTES_DIR.glob("*.txt")]
        return "Notebooks: " + ", ".join(books) if books else "No notebooks yet."

    return f"Unknown notes action: '{action}'. Use append, read, clear, or list."
