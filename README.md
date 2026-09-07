# JARVIS

<p align="center">
  <strong>Your Personal AI Assistant</strong><br>
  Think • Understand • Automate • Execute
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python" alt="Python 3.13">
  <img src="https://img.shields.io/badge/AI-Powered-purple?style=for-the-badge" alt="AI Powered">
  <img src="https://img.shields.io/badge/Platform-Windows-success?style=for-the-badge&logo=windows" alt="Windows">
</p>

---

## What is JARVIS?

**JARVIS** is a Python-powered personal AI assistant designed to combine **AI conversation, voice interaction, computer automation, browser control, web search, file processing, and developer assistance** into one intelligent assistant.

> ⚡ For the complete JARVIS experience, run it locally on your Windows computer.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **AI Assistant** | Natural-language conversations and intelligent responses |
| 🎙️ **Voice Control** | Voice input and text-to-speech |
| 🖥️ **Desktop Control** | Interact with your computer |
| 🖱️ **Mouse & Keyboard** | Automate mouse and keyboard actions |
| 🌐 **Browser Automation** | Browser control with Playwright |
| 🔎 **Web Search** | Search and retrieve online information |
| 📁 **File Processing** | Work with files and documents |
| 👨‍💻 **Developer Assistant** | Coding and development assistance |
| 📺 **YouTube Tools** | YouTube-related tools |
| 🔔 **Reminders** | Create and manage reminders |
| 🧠 **Memory** | Store and manage assistant information |
| 🔐 **AI Providers** | Gemini and OpenRouter support |

---

# 📥 Getting Started

## ⚠️ New Users — Start Here

**You must download the ZIP file from GitHub and extract it before running JARVIS.**

JARVIS is currently distributed as a Python project and is **not yet a standalone `.exe` application**.

### 1️⃣ Open the Repository

Go to:

**https://github.com/brandon-wrld/jarvis-brandon**

### 2️⃣ Download the ZIP

On the GitHub repository page:

**Code → Download ZIP**

Your browser will normally save the file to:

```text
Downloads/
```

The file will look similar to:

```text
jarvis-brandon-main.zip
```

### 3️⃣ Extract the ZIP

Open your Downloads folder.

Right-click:

```text
jarvis-brandon-main.zip
```

Select:

```text
Extract All...
```

Extract it somewhere convenient, such as your Desktop.

You should now have:

```text
Desktop/
└── jarvis-brandon-main/
    ├── actions/
    ├── agent/
    ├── config/
    ├── core/
    ├── memory/
    ├── .env.example
    ├── main.py
    ├── requirements.txt
    ├── setup.py
    └── README.md
```

### 🚨 Important

**Do not run JARVIS from inside the ZIP file.**

Always:

```text
Download ZIP
     ↓
Extract ZIP
     ↓
Open extracted folder
     ↓
Install dependencies
     ↓
Configure API keys
     ↓
Run JARVIS
```

---

# 🪟 Windows Installation

Windows is currently the **recommended platform** for the complete JARVIS experience.

This allows JARVIS to interact with your local:

```text
🎤 Microphone
🔊 Speakers
🖥️ Screen
🖱️ Mouse
⌨️ Keyboard
🪟 Windows Applications
🌐 Browser
```

## Requirements

- Windows 10 or Windows 11
- Python 3.13
- Internet connection
- Working microphone
- Speakers or headphones

---

## 1️⃣ Open the JARVIS Folder

After extracting the ZIP, open the extracted folder.

Example:

```text
C:\Users\YourName\Desktop\jarvis-brandon-main
```

Make sure you can see:

```text
main.py
requirements.txt
setup.py
actions/
agent/
config/
core/
memory/
```

---

## 2️⃣ Open PowerShell

Open the JARVIS folder in File Explorer.

Click the address bar and type:

```text
powershell 
Run in Virtual Studio (recommended)
# 2. Clone Brandon's JARVIS repository
git clone https://github.com/brandon-wrld/jarvis-brandon.git

```

Press **Enter**.

Check that you are in the correct folder:

```powershell
cd maina
dir
```

You should see:

```text
main.py
requirements.txt
```

---

## 3️⃣ Create a Virtual Environment

```powershell
py install 3.13
py -3.13 -m venv .venv
```

---

## 4️⃣ Activate the Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see:

```text
(.venv) PS C:\Users\YourName\Desktop\jarvis-brandon-main>
```

### If PowerShell blocks activation

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

# 📦 Install Dependencies

Upgrade pip:

```powershell
python -m pip install --upgrade pip setuptools wheel
```

Install JARVIS dependencies:

```powershell
pip install -r requirements.txt
```

Install the browser required by Playwright:

```powershell
python -m playwright install chromium
```

---

# 🔑 API Configuration

JARVIS requires AI API access.

Inside the project you will find:

```text
.env.example
```

Create a copy named:

```text
.env
```

Then add your own API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

Replace the placeholders with your own keys.

## 🔐 Security

**Never upload your `.env` file or real API keys to GitHub.**

Keep these files private:

```text
.env
config/api_keys.json
```

Each user should use their **own API keys**.

---

# ▶️ Launch JARVIS

Make sure the virtual environment is active:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then:

```powershell
python main.py
```

🚀 **JARVIS should now start.**

---

# 🎤 Test Your Microphone

Run:

```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

Your microphone should appear in the list.

If it does not, check:

**Windows Settings → System → Sound → Input**

Also make sure Windows microphone permissions are enabled.

---

# 🖱️ Test Computer Control

JARVIS uses PyAutoGUI for computer interaction.

Run:

```powershell
python -c "import pyautogui; print(pyautogui.size())"
```

A successful result should display your screen resolution, for example:

```text
Size(width=1920, height=1080)
```

---

# 🌐 Browser Automation

JARVIS uses Playwright for browser automation.

If Chromium is missing, run:

```powershell
python -m playwright install chromium
```

Then:

```powershell
python main.py
```

---

# ☁️ GitHub Codespaces

## ⚠️ Why Codespaces Cannot Run the Full JARVIS Experience

GitHub Codespaces is excellent for **developing JARVIS**, but it is not recommended for running the complete desktop assistant.

### Why?

Codespaces runs your project on a **remote Linux computer in the cloud**, not directly on your physical computer.

When you run:

```bash
python main.py
```

inside Codespaces, JARVIS is running on GitHub's remote machine.

That remote machine does not automatically have access to your physical computer's hardware.

Therefore, it cannot normally control your:

- 🎤 Physical microphone
- 🔊 Physical speakers
- 🖥️ Windows screen
- 🖱️ Physical mouse
- ⌨️ Physical keyboard
- 📷 Webcam
- 🪟 Windows applications

### What about `DISPLAY` and `XAUTHORITY`?

You may see solutions using:

```env
DISPLAY=:99
XAUTHORITY=/tmp/.Xauthority
```

These can configure a **virtual display inside the Codespace**.

They do **not** connect that virtual display to your physical Windows screen.

For example:

```text
        YOUR WINDOWS PC
┌──────────────────────────┐
│ 🖥️ Real Screen           │
│ 🎤 Real Microphone       │
│ 🔊 Real Speakers         │
│ 🖱️ Real Mouse            │
│ ⌨️ Real Keyboard         │
└────────────┬─────────────┘
             │
          Internet
             │
             ▼
      GITHUB CODESPACE
┌──────────────────────────┐
│ 🐧 Remote Linux Machine  │
│                          │
│ 🤖 JARVIS                │
│ Virtual Display          │
└──────────────────────────┘
```

A virtual display exists **inside the remote Linux machine**. It is not your actual Windows desktop.

The same applies to audio. Installing PortAudio or other Linux audio packages can make audio devices available inside the remote environment, but it does not automatically connect JARVIS to the microphone and speakers physically connected to your Windows computer.

### ✅ Recommended setup

**Use Codespaces for development.**

**Download the ZIP, extract it, install it, and run JARVIS locally on Windows for the full experience.**

---

# 🏗️ Architecture

```text
                    👤 USER
                      │
                      ▼
              ┌───────────────┐
              │     JARVIS    │
              │     INPUT     │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ AI / PLANNER  │
              └───────┬───────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
   🖥️ Computer    🌐 Browser    👨‍💻 Developer
    Control       Automation       Tools
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
              ┌───────────────┐
              │    RESPONSE   │
              └───────────────┘
```

---

# 📂 Project Structure

```text
jarvis-brandon/
│
├── actions/
│   ├── browser_control.py
│   ├── code_helper.py
│   ├── computer_control.py
│   ├── computer_settings.py
│   ├── desktop.py
│   ├── dev_agent.py
│   ├── file_controller.py
│   ├── file_processor.py
│   ├── flight_finder.py
│   ├── game_updater.py
│   ├── open_app.py
│   ├── reminder.py
│   ├── screen_processor.py
│   ├── send_message.py
│   ├── weather_report.py
│   ├── web_search.py
│   └── youtube_video.py
│
├── agent/
│   ├── error_handler.py
│   ├── executor.py
│   ├── planner.py
│   └── task_queue.py
│
├── config/
├── core/
├── memory/
│
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
├── setup.py
└── README.md
```

---

# 🛠️ Troubleshooting

### ❌ Python is not recognized

Check:

```powershell
py --version
```

Python 3.13 is recommended.

### ❌ `ModuleNotFoundError`

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then:

```powershell
pip install -r requirements.txt
```

### ❌ Playwright error

Run:

```powershell
python -m playwright install chromium
```

### ❌ Microphone not detected

Check:

**Windows Settings → System → Sound → Input**

Then:

```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### ❌ JARVIS does not start

Run:

```powershell
python main.py
```

Read the complete error displayed in PowerShell.

When requesting support, provide the **complete traceback** and never include your API keys.

---

# 🛣️ Roadmap

### Current

- [x] AI conversations
- [x] Computer automation
- [x] Browser automation
- [x] Web search
- [x] Voice capabilities
- [x] File processing
- [x] Developer tools
- [x] Memory system
- [x] Gemini support
- [x] OpenRouter support

### Future

- [ ] Advanced wake-word detection
- [ ] Improved long-term memory
- [ ] More AI providers
- [ ] Advanced browser automation
- [ ] Plugin architecture
- [ ] Improved GUI
- [ ] Linux desktop support
- [ ] macOS support
- [ ] First-run setup wizard
- [ ] Automatic updates
- [ ] One-click Windows installer
- [ ] Standalone `.exe` application

---

# 🤝 Contributing

Contributions are welcome!

Clone the repository:

```bash
git clone https://github.com/brandon-wrld/jarvis-brandon.git
```

Create a feature branch:

```bash
git checkout -b feature/my-feature
```

Make your changes, test them, and submit a pull request.

---

# 🐛 Issues & Support

Found a bug?

Open an issue:

**https://github.com/brandon-wrld/jarvis-brandon/issues**

When reporting an issue, include:

- Operating system
- Python version
- Error message
- Steps to reproduce the problem

**Never include API keys.**

---

# ⭐ Support the Project

If you find JARVIS useful:

⭐ **Star the repository**  
🍴 **Fork the project**  
🐛 **Report bugs**  
💡 **Suggest features**  
🤝 **Contribute**

---

# 👨‍💻 Author

## Brandon Maina

GitHub:

**https://github.com/brandon-wrld**

Project:

**https://github.com/brandon-wrld/jarvis-brandon**

---

<p align="center">

# JARVIS

### Think. Understand. Automate. Execute.

**Built with Python + AI**

⭐ Star the project if you find it useful!

</p>
