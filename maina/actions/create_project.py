import time
import webbrowser

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE    = 0.05
    _PYAUTOGUI = True
except ImportError:
    _PYAUTOGUI = False

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False


CLAUDE_NEW_CHAT_URL = "https://claude.ai/new"

# Seconds to wait for the browser + page to be ready before typing.
# Slow machines / cold browser starts need more time here — tune if
# JARVIS keeps typing into the wrong window.
_PAGE_LOAD_WAIT = 3.5


def create_project(
    parameters: dict,
    player=None,
    session_memory=None,
) -> str:
    """
    Opens Claude in the default browser and types the user's project
    prompt into the message box, ready to send.

    parameters:
      prompt      : string (required) — what to build/create
      auto_send   : bool (optional, default False) — press Enter after typing
    """
    params    = parameters or {}
    prompt    = (params.get("prompt") or "").strip()
    auto_send = bool(params.get("auto_send", False))

    if not prompt:
        msg = "Sir, I need to know what the project should be about."
        _log(msg, player)
        return msg

    if not _PYAUTOGUI:
        msg = "Sir, I can't type the prompt — PyAutoGUI isn't installed."
        _log(msg, player)
        return msg

    try:
        opened = webbrowser.open(CLAUDE_NEW_CHAT_URL)
        if not opened:
            raise RuntimeError("webbrowser.open returned False")
    except Exception as e:
        msg = f"Sir, I couldn't open Claude: {e}"
        _log(msg, player)
        return msg

    # Give the browser time to launch/focus and the page time to load
    # before we start sending keystrokes.
    time.sleep(_PAGE_LOAD_WAIT)

    try:
        if len(prompt) > 20 and _PYPERCLIP:
            pyperclip.copy(prompt)
            time.sleep(0.1)
            pyautogui.hotkey("ctrl", "v")
        else:
            pyautogui.typewrite(prompt, interval=0.03)
    except Exception as e:
        msg = f"Sir, I opened Claude but couldn't type the prompt: {e}"
        _log(msg, player)
        return msg

    if auto_send:
        time.sleep(0.3)
        pyautogui.press("enter")
        msg = f"Sir, I've opened Claude and sent the project prompt."
    else:
        msg = f"Sir, I've opened Claude and typed the project prompt — ready for you to send it."

    _log(msg, player)

    if session_memory:
        try:
            session_memory.set_last_search(query=prompt, response=msg)
        except Exception:
            pass

    return msg


def _log(message: str, player=None) -> None:
    print(f"[CreateProject] {message}")
    if player:
        try:
            player.write_log(f"JARVIS: {message}")
        except Exception:
            pass
