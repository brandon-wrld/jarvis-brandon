# Adding the new skills to Brandon's JARVIS

8 new action files, each following the exact pattern used by your existing
`actions/*.py` files:

```python
def <name>(parameters=None, response=None, player=None, session_memory=None) -> str:
    ...
```

| File | Skill | Extra dependency |
|---|---|---|
| `actions/github_repo.py` | Create a GitHub repo | `requests`, a GitHub token |
| `actions/ai_tools.py` | Open ChatGPT / Gemini / Perplexity / etc. and optionally send a prompt | none (reuses `browser_control`) |
| `actions/spotify_control.py` | Play a playlist/song, pause, skip, volume | `spotipy`, Spotify API creds |
| `actions/screenshot_tool.py` | Screenshot, optional label, save to folder | `pyautogui`, `Pillow` |
| `actions/calendar_event.py` | Real calendar event (not a reminder) | `google-api-python-client` + OAuth, else falls back to `.ics` |
| `actions/email_draft.py` | Open Gmail/mail client with fields filled | none |
| `actions/clipboard_manager.py` | Save/recall named snippets | `pyperclip` |
| `actions/notes.py` | Append/read a running notes file | none |

Drop all 8 files into `maina/actions/`.

---

## 1. Wire them into `main.py` (the live voice-loop / function-calling path)

### 1a. Imports (near the top, with the other `from actions.X import Y` lines)

```python
from actions.github_repo       import github_repo
from actions.ai_tools          import ai_tools
from actions.spotify_control   import spotify_control
from actions.screenshot_tool   import screenshot_tool
from actions.calendar_event    import calendar_event
from actions.email_draft       import email_draft
from actions.clipboard_manager import clipboard_manager
from actions.notes             import notes
```

### 1b. Add entries to `TOOL_DECLARATIONS`

Append these dicts to the `TOOL_DECLARATIONS` list (same shape as `open_app`,
`weather_report`, etc.):

```python
    {
        "name": "github_repo",
        "description": "Creates a new GitHub repository.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "name":        {"type": "STRING", "description": "Repository name"},
                "description": {"type": "STRING", "description": "Repository description"},
                "private":     {"type": "BOOLEAN", "description": "Whether the repo is private"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "ai_tools",
        "description": "Opens a web-based AI assistant (ChatGPT, Gemini, Claude, Perplexity, etc.) and optionally sends it a prompt.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "tool":   {"type": "STRING", "description": "Which AI tool: chatgpt, claude, gemini, perplexity, copilot, grok, etc."},
                "prompt": {"type": "STRING", "description": "Prompt text to send, if any"}
            },
            "required": ["tool"]
        }
    },
    {
        "name": "spotify_control",
        "description": "Controls Spotify: play a song/playlist by name, pause, skip, set volume.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "play | pause | next | previous | volume"},
                "query":  {"type": "STRING", "description": "Song, artist, or playlist name (for play)"},
                "level":  {"type": "NUMBER", "description": "0-100 (for volume)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "screenshot_tool",
        "description": "Takes a screenshot and saves it, optionally with a label, to a chosen folder.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "folder":   {"type": "STRING", "description": "desktop | downloads | documents | pictures | full path"},
                "filename": {"type": "STRING", "description": "Optional file name"},
                "label":    {"type": "STRING", "description": "Optional text label drawn on the screenshot"}
            },
            "required": []
        }
    },
    {
        "name": "calendar_event",
        "description": "Creates a real calendar event with a start time and duration (not a plain reminder).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "title":            {"type": "STRING", "description": "Event title"},
                "date":             {"type": "STRING", "description": "YYYY-MM-DD"},
                "time":             {"type": "STRING", "description": "HH:MM, 24h"},
                "duration_minutes": {"type": "NUMBER", "description": "Length of the event in minutes"},
                "location":         {"type": "STRING", "description": "Optional location"},
                "description":      {"type": "STRING", "description": "Optional event notes"}
            },
            "required": ["title", "date"]
        }
    },
    {
        "name": "email_draft",
        "description": "Opens Gmail or the default mail client with a new message pre-filled.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "to":      {"type": "STRING", "description": "Recipient email address"},
                "subject": {"type": "STRING", "description": "Email subject"},
                "body":    {"type": "STRING", "description": "Email body text"}
            },
            "required": ["to"]
        }
    },
    {
        "name": "clipboard_manager",
        "description": "Saves or recalls named clipboard snippets.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "save | recall | list | delete"},
                "name":   {"type": "STRING", "description": "Snippet name"},
                "text":   {"type": "STRING", "description": "Text to save (optional; defaults to current clipboard)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "notes",
        "description": "Appends to or reads back a running notes file.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":   {"type": "STRING", "description": "append | read | clear | list"},
                "notebook": {"type": "STRING", "description": "Notebook name, default 'general'"},
                "text":     {"type": "STRING", "description": "Text to append"}
            },
            "required": ["action"]
        }
    },
```

### 1c. Add dispatch branches

In the big `if name == "open_app": ... elif name == ...` block (~line 590),
add:

```python
            elif name == "github_repo":
                r = await loop.run_in_executor(None, lambda: github_repo(parameters=args, player=self.ui))
                result = r or "Repository created."

            elif name == "ai_tools":
                r = await loop.run_in_executor(None, lambda: ai_tools(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "spotify_control":
                r = await loop.run_in_executor(None, lambda: spotify_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "screenshot_tool":
                r = await loop.run_in_executor(None, lambda: screenshot_tool(parameters=args, player=self.ui))
                result = r or "Screenshot taken."

            elif name == "calendar_event":
                r = await loop.run_in_executor(None, lambda: calendar_event(parameters=args, player=self.ui))
                result = r or "Event created."

            elif name == "email_draft":
                r = await loop.run_in_executor(None, lambda: email_draft(parameters=args, player=self.ui))
                result = r or "Draft opened."

            elif name == "clipboard_manager":
                r = await loop.run_in_executor(None, lambda: clipboard_manager(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "notes":
                r = await loop.run_in_executor(None, lambda: notes(parameters=args, player=self.ui))
                result = r or "Done."
```

---

## 2. Wire them into `agent/executor.py` (the multi-step planner path)

Find the chain of `if tool == "open_app": ...` (~line 176) and add matching
branches, e.g.:

```python
    if tool == "github_repo":
        from actions.github_repo import github_repo
        return github_repo(parameters=parameters, player=None) or "Done."

    if tool == "ai_tools":
        from actions.ai_tools import ai_tools
        return ai_tools(parameters=parameters, player=None) or "Done."

    if tool == "spotify_control":
        from actions.spotify_control import spotify_control
        return spotify_control(parameters=parameters, player=None) or "Done."

    if tool == "screenshot_tool":
        from actions.screenshot_tool import screenshot_tool
        return screenshot_tool(parameters=parameters, player=None) or "Done."

    if tool == "calendar_event":
        from actions.calendar_event import calendar_event
        return calendar_event(parameters=parameters, player=None) or "Done."

    if tool == "email_draft":
        from actions.email_draft import email_draft
        return email_draft(parameters=parameters, player=None) or "Done."

    if tool == "clipboard_manager":
        from actions.clipboard_manager import clipboard_manager
        return clipboard_manager(parameters=parameters, player=None) or "Done."

    if tool == "notes":
        from actions.notes import notes
        return notes(parameters=parameters, player=None) or "Done."
```

---

## 3. Tell the planner about them: `agent/planner.py`

Add to `PLANNER_PROMPT`'s `AVAILABLE TOOLS AND THEIR PARAMETERS` section:

```
github_repo
  name: string (required)
  description: string (optional)
  private: boolean (optional)

ai_tools
  tool: string (required) — chatgpt | claude | gemini | perplexity | copilot | grok | deepseek | mistral
  prompt: string (optional)

spotify_control
  action: "play" | "pause" | "next" | "previous" | "volume" (required)
  query: string (for play)
  level: int 0-100 (for volume)

screenshot_tool
  folder: string (optional, default "desktop")
  filename: string (optional)
  label: string (optional)

calendar_event
  title: string (required)
  date: string YYYY-MM-DD (required)
  time: string HH:MM (optional, default 09:00)
  duration_minutes: int (optional, default 60)
  location: string (optional)
  description: string (optional)

email_draft
  to: string (required)
  subject: string (optional)
  body: string (optional)

clipboard_manager
  action: "save" | "recall" | "list" | "delete" (required)
  name: string (required for save/recall/delete)
  text: string (optional, for save)

notes
  action: "append" | "read" | "clear" | "list" (required)
  notebook: string (optional, default "general")
  text: string (required for append)
```

(Optional) add one or two matching examples in the `EXAMPLES:` block, e.g.:

```
Goal: "Create a private GitHub repo called jarvis-plugins"
Steps:

github_repo | name: "jarvis-plugins", private: true

Goal: "Play Lo-Fi Beats on Spotify"
Steps:

spotify_control | action: play, query: "Lo-Fi Beats"
```

---

## 4. New dependencies

Add to `requirements.txt`:

```
requests
spotipy
pyautogui
Pillow
pyperclip
google-api-python-client
google-auth-oauthlib
```

(`pyautogui`, `Pillow`, and `google-*` are optional — each new action
degrades gracefully and returns a helpful message if its dependency or
API credentials are missing, instead of crashing.)

## 5. Config additions (`config/api_keys.json`)

```json
{
  "github_token": "ghp_xxx...",
  "spotify_client_id": "...",
  "spotify_client_secret": "...",
  "spotify_redirect_uri": "http://127.0.0.1:8080/callback"
}
```

For `calendar_event`'s Google Calendar path, drop your OAuth client file at
`config/google_client_secret.json` (downloaded from Google Cloud Console);
the first run will open a browser to authorize and cache a token at
`config/calendar_token.json`. Without it, the action just falls back to
generating and opening a `.ics` file — no setup required.
