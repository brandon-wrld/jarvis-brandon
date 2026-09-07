"""
ai_tools.py — Opens web-based AI assistants (ChatGPT, Gemini, Perplexity, etc.)
in the user's browser, optionally pre-filling and submitting a prompt.

Reuses actions.browser_control so it benefits from the same persistent
real-profile browser sessions (stays logged in, etc.) as the rest of JARVIS.
"""

from actions.browser_control import browser_control

_AI_SITES: dict[str, str] = {
    "chatgpt":     "https://chat.openai.com",
    "gpt":         "https://chat.openai.com",
    "openai":      "https://chat.openai.com",
    "claude":      "https://claude.ai",
    "gemini":      "https://gemini.google.com",
    "bard":        "https://gemini.google.com",
    "perplexity":  "https://www.perplexity.ai",
    "copilot":     "https://copilot.microsoft.com",
    "grok":        "https://grok.com",
    "deepseek":    "https://chat.deepseek.com",
    "mistral":     "https://chat.mistral.ai",
    "poe":         "https://poe.com",
    "huggingchat": "https://huggingface.co/chat",
}

# Best-effort selectors for the main prompt textbox on each site.
# smart_type() in browser_control already tries several strategies
# (placeholder / label / role), so these are just descriptive hints.
_PROMPT_HINTS: dict[str, str] = {
    "chatgpt":    "Message ChatGPT",
    "claude":     "How can Claude help you today",
    "gemini":     "Enter a prompt here",
    "perplexity": "Ask anything",
    "copilot":    "Ask me anything",
    "grok":       "Ask Grok anything",
    "deepseek":   "Send a message",
    "mistral":    "Ask le Chat",
    "poe":        "Talk to",
}


def _resolve(tool_name: str) -> tuple[str, str]:
    key = tool_name.lower().strip()
    for alias, url in _AI_SITES.items():
        if alias in key or key in alias:
            return alias, url
    return "chatgpt", _AI_SITES["chatgpt"]


def ai_tools(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    params = parameters or {}
    tool_name = (params.get("tool") or "chatgpt").strip()
    prompt = params.get("prompt", "").strip()
    browser = params.get("browser")

    alias, url = _resolve(tool_name)

    if player:
        player.write_log(f"[ai_tools] {alias}")

    # 1. Navigate to the AI tool.
    nav_result = browser_control(
        parameters={"action": "go_to", "url": url, "browser": browser},
        player=player,
    )

    if not prompt:
        return nav_result

    # 2. Type the prompt into the input box.
    hint = _PROMPT_HINTS.get(alias, "Message")
    type_result = browser_control(
        parameters={"action": "smart_type", "description": hint, "text": prompt, "browser": browser},
        player=player,
    )

    # 3. Submit with Enter.
    browser_control(parameters={"action": "press", "key": "Enter", "browser": browser}, player=player)

    return f"Opened {alias} and sent prompt. ({nav_result} / {type_result})"
