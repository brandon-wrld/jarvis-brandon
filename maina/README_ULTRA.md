# 🤖 MARK XXXIX ULTRA — Multi-Agent Edition


A massively upgraded version of the JARVIS AI assistant, now featuring a **3-window multi-agent system** with zero errors.

---

## 🆕 What's New in ULTRA

### 🪟 Three Separate Windows
| Window | Position | Purpose |
|--------|----------|---------|
| **J.A.R.V.I.S Main** | Screen centre | Voice AI, tools, full system control |
| **⬡ Microline Scientific Solutions Ltd** | Top-right | Lab science, chemistry, molecular analysis |
| **✎ Assignment Helper** | Top-left | Essays, research, academic support |

### 🎨 Visual Upgrades
- **Hex grid background** on HUD canvas — ambient Iron Man aesthetic
- **4 spinning arc rings** (up from 3) with depth layering
- **Third counter-scanner** arc adds visual complexity
- **Dual agent link indicators** on HUD (bottom corners)
- **Hex decoration nodes** scattered across HUD background
- Bigger, more animated waveform (40 bars vs 36)
- Enhanced particle burst system when speaking
- **Microline green** palette — scientific, bio-lab aesthetic
- **Assignment purple** palette — academic, scholarly aesthetic

### ⚙️ Functional Upgrades
- **Quick command buttons** (Volume Up/Down, Screenshot)
- **Subject selector** in Assignment Helper (12 subjects)
- **Quick prompt buttons** in Assignment Helper (Summarise, Essay Plan, Cite)
- **F1 / F2 keyboard shortcuts** to open/focus agent windows
- Agent status panel in left sidebar (shows ONLINE/PROCESSING state)
- Agent launch buttons in right panel
- Anthropic Claude API integration for both agents
- Improved typewriter speed (5ms per char vs 6ms)
- Enhanced setup dialog with larger, cleaner layout

---

## 🚀 Quick Start

```bash
# Same as original — no extra dependencies needed
pip install -r requirements.txt
playwright install
python main.py
```

### Agent API Keys (Optional)
To enable the Microline & Assignment agent responses, add your Anthropic API key to `config/api_keys.json`:

```json
{
  "gemini_api_key": "YOUR_GEMINI_KEY",
  "os_system": "windows",
  "anthropic_api_key": "YOUR_ANTHROPIC_KEY"
}
```

Without the Anthropic key, agent windows still open and display the UI — you just won't get AI responses.
### Microline Knowledge Sources

Microline answers are grounded in the official public website and the Microline portal. The agent refreshes
those sources periodically and labels them in its internal context before generating a professional summary.
The deployed portal's admin route currently depends on Supabase authentication. To include authenticated
portal tables such as inventory, deliveries, invoices, sales, and clients, set these variables in the same
PowerShell session used to start JARVIS:

```powershell
$env:MICROLINE_PORTAL_EMAIL = "your-admin-email"
$env:MICROLINE_PORTAL_PASSWORD = "your-admin-password"
python main.py
```

Credentials are read only from the process environment and are not written to the repository or sent to
Gemini. If they are absent or the portal is unavailable, Microline uses the official public sources and
clearly states when requested information is not available.

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| F1  | Open Microline Scientific window (top-right) |
| F2  | Open Assignment Helper window (top-left) |
| F4  | Toggle microphone mute |
| F11 | Toggle fullscreen |

---

## 🪟 Window Layout

```
┌─────────────────┐         ┌──────────────────────────┐
│  ✎ Assignment   │         │  ⬡ Microline Scientific  │
│  Helper         │         │  Solutions Ltd            │
│  (top-left)     │         │  (top-right)              │
└─────────────────┘         └──────────────────────────┘

              ┌─────────────────────────┐
              │                         │
              │   J.A.R.V.I.S MAIN      │
              │   (centre screen)        │
              │                         │
              └─────────────────────────┘
```

---

## 📋 Requirements

Same as original MARK XXXIX:

| Requirement | Details |
|---|---|
| **OS** | Windows 10/11, macOS, or Linux |
| **Python** | 3.11 or 3.12 |
| **Microphone** | Required for voice interaction |
| **API Key** | Free Gemini API key (+ optional Anthropic key for agents) |

---

## ⚠️ License

Personal and non-commercial use only.
Licensed under **[Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)**.
