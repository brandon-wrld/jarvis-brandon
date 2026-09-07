"""
screenshot_tool.py — Takes a screenshot, optionally annotates it with a
red box + label, and saves it to a chosen (or default) folder.
"""

import platform
import time
from datetime import datetime
from pathlib import Path

try:
    import pyautogui
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

try:
    from PIL import ImageDraw, ImageFont
    _PIL = True
except ImportError:
    _PIL = False

_SYSTEM = platform.system()

_FOLDER_ALIASES = {
    "desktop":   lambda: Path.home() / "Desktop",
    "downloads": lambda: Path.home() / "Downloads",
    "documents": lambda: Path.home() / "Documents",
    "pictures":  lambda: Path.home() / "Pictures",
}


def _resolve_folder(raw: str) -> Path:
    key = (raw or "desktop").lower().strip()
    resolver = _FOLDER_ALIASES.get(key)
    folder = resolver() if resolver else Path(raw).expanduser()
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def screenshot_tool(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    folder_raw = params.get("folder", "desktop")
    filename = params.get("filename", "").strip()
    label = params.get("label", "").strip()
    region = params.get("region")  # optional [x, y, w, h]

    if not _PYAUTOGUI:
        return "pyautogui isn't installed (pip install pyautogui), so I can't take a screenshot."

    folder = _resolve_folder(folder_raw)
    if not filename:
        filename = f"jarvis_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    if not filename.lower().endswith(".png"):
        filename += ".png"
    save_path = folder / filename

    if player:
        player.write_log(f"[screenshot_tool] -> {save_path}")

    try:
        time.sleep(float(params.get("delay", 0)))
        if region and len(region) == 4:
            img = pyautogui.screenshot(region=tuple(region))
        else:
            img = pyautogui.screenshot()

        if label and _PIL:
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 28)
            except Exception:
                font = ImageFont.load_default()
            draw.rectangle([10, 10, 20 + len(label) * 15, 50], fill=(255, 0, 0))
            draw.text((15, 15), label, fill=(255, 255, 255), font=font)

        img.save(save_path)
        return f"Screenshot saved to {save_path}"
    except Exception as e:
        return f"Screenshot failed: {e}"
