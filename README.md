# 🤖 JARVIS

> **Your personal AI assistant — built to understand, automate, and help you get things done.**

JARVIS is a Python-powered personal AI assistant designed to combine **AI conversation, voice interaction, computer automation, browser control, web search, file processing, and developer assistance** into one intelligent assistant.

---

## ✨ Features

- 🧠 AI-powered conversations
- 🎙️ Voice interaction
- 💻 Computer automation
- 🖱️ Mouse and keyboard control
- 🖥️ Screen interaction
- 🌐 Browser automation
- 🔎 Web searching
- 📁 File and document processing
- 👨‍💻 Coding assistance
- 📺 YouTube tools
- 🔔 Reminders
- 🧠 Memory and task management
- 🔐 Gemini and OpenRouter support

---

# 📥 How to Get JARVIS

## ⚠️ Important for New Users

**You must download the JARVIS ZIP file and extract it before you can run it.**

JARVIS is currently provided as a Python project. It is **not yet a standalone `.exe` application**.

### Step 1 — Open the GitHub Repository

Go to:

👉 https://github.com/brandon-wrld/jarvis-brandon

### Step 2 — Download the ZIP

On the GitHub repository:

1. Click the **Code** button.
2. Click **Download ZIP**.
3. Your browser will download the project.

The ZIP will normally be saved in your:

```text
Downloads

folder.

The file will look similar to:

jarvis-brandon-main.zip
Step 3 — Extract the ZIP

Go to your Downloads folder.

Right-click:

jarvis-brandon-main.zip

Select:

Extract All...

Choose somewhere convenient, such as:

Desktop

After extraction, you should have:

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
🚨 IMPORTANT

Do not try to run JARVIS from inside the ZIP file.

Always:

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
🪟 Windows Installation

Windows is currently the recommended platform for running the complete JARVIS experience.

This is because JARVIS can interact with your local:

🎤 Microphone
🔊 Speakers
🖥️ Screen
🖱️ Mouse
⌨️ Keyboard
🪟 Windows applications
Requirements

Before installing JARVIS, install:

Windows 10 or Windows 11
Python 3.13
Internet connection
Working microphone
Speakers or headphones
🚀 Installation
1. Open the JARVIS folder

After extracting the ZIP, open the extracted folder.

For example:

C:\Users\YourName\Desktop\jarvis-brandon-main

You should see:

main.py
requirements.txt
setup.py
actions/
agent/
config/
core/
memory/
2. Open PowerShell

Open the JARVIS folder using File Explorer.

Click the address bar and type:

powershell

Press Enter.

Check that you are inside the JARVIS folder:

dir

You should see:

main.py
requirements.txt
3. Create a virtual environment

Run:

py -3.13 -m venv .venv

This creates a separate Python environment for JARVIS.

4. Activate the virtual environment

Run:

.\.venv\Scripts\Activate.ps1

You should see:

(.venv) PS C:\Users\YourName\Desktop\jarvis-brandon-main>
If PowerShell blocks activation

Run:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Then activate again:

.\.venv\Scripts\Activate.ps1
📦 Install Dependencies

Upgrade pip:

python -m pip install --upgrade pip setuptools wheel

Install the JARVIS dependencies:

pip install -r requirements.txt

This may take several minutes.

🌐 Install Browser Support

JARVIS uses Playwright for browser automation.

Install Chromium:

python -m playwright install chromium
🔑 Configure Your API Keys

JARVIS uses AI services such as Gemini and OpenRouter.

Inside the project folder you will find:

.env.example

Create a copy of this file and rename it:

.env

Your folder should contain:

jarvis-brandon-main/
├── .env
├── .env.example
├── main.py
└── ...

Open .env and enter your own API keys:

GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

Replace the placeholder values with your actual API keys.

🔐 IMPORTANT SECURITY WARNING

Never upload your API keys to GitHub.

Do not publish:

.env
config/api_keys.json

Do not share API keys through:

GitHub
WhatsApp
Discord
Screenshots
Social media
Public repositories

Each user should use their own API keys.

If you accidentally expose an API key, revoke it immediately and generate a new one.

▶️ Run JARVIS

Make sure your virtual environment is active:

.\.venv\Scripts\Activate.ps1

Then run:

python main.py

JARVIS will start.

🎤 Test Your Microphone

Before using voice features, check whether Python can detect your audio devices:

python -c "import sounddevice as sd; print(sd.query_devices())"

Your microphone should appear in the list.

If Windows does not detect your microphone, check:

Settings
→ System
→ Sound
→ Input

Also make sure microphone permissions are enabled.

🖱️ Test Computer Control

JARVIS uses PyAutoGUI for computer interaction.

Test it with:

python -c "import pyautogui; print(pyautogui.size())"

A successful result should display your screen resolution, for example:

Size(width=1920, height=1080)
☁️ GitHub Codespaces
⚠️ Why Codespaces Cannot Run the Full JARVIS Experience

GitHub Codespaces is excellent for developing JARVIS, but it is not recommended for running the complete desktop assistant.

The reason is simple:

Codespaces runs JARVIS on a remote Linux computer in the cloud, not directly on your physical computer.

For example:

             YOUR COMPUTER
        ┌─────────────────────┐
        │ 🖥️ Real screen      │
        │ 🎤 Real microphone  │
        │ 🔊 Real speakers    │
        │ 🖱️ Real mouse       │
        │ ⌨️ Real keyboard    │
        └──────────┬──────────┘
                   │
                Internet
                   │
                   ▼
          GITHUB CODESPACE
        ┌─────────────────────┐
        │ 🐧 Remote Linux     │
        │                     │
        │ 🤖 JARVIS          │
        │ Virtual environment │
        └─────────────────────┘

When you run:

python main.py

inside Codespaces, JARVIS is running on the remote Linux machine.

It therefore does not automatically have access to your physical:

🎤 Microphone
🔊 Speakers
🖥️ Windows screen
🖱️ Mouse
⌨️ Keyboard
📷 Webcam
🪟 Windows applications
❓ What about DISPLAY and XAUTHORITY?

You may see solutions that configure:

DISPLAY=:99
XAUTHORITY=/tmp/.Xauthority

These variables can create or configure a virtual display inside the Codespace.

However, they do not connect that virtual display to your physical Windows computer.

For example:

DISPLAY=:99

means:

Use display :99 inside the remote Linux environment.

It does not mean:

Control the Windows screen sitting in front of the user.

The same applies to audio.

Installing a Linux audio library such as PortAudio can allow Python to communicate with audio devices available inside the remote environment, but it does not automatically connect JARVIS to the microphone and speakers physically connected to your Windows computer.

✅ Therefore:

Use GitHub Codespaces for development.

Use your local Windows computer to run JARVIS with full voice and computer-control capabilities.

🧪 Troubleshooting
Python is not recognized

Check your Python version:

py --version

Python 3.13 is recommended.

ModuleNotFoundError

Make sure the virtual environment is active:

.\.venv\Scripts\Activate.ps1

Then reinstall:

pip install -r requirements.txt
Playwright browser error

Run:

python -m playwright install chromium
Microphone not detected

Check:

Windows Settings
→ System
→ Sound
→ Input

Then run:

python -c "import sounddevice as sd; print(sd.query_devices())"
JARVIS does not start

Run:

python main.py

Read the complete error displayed in PowerShell.

When requesting support, provide the full traceback so the problem can be diagnosed correctly.

📂 Project Structure
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
│
├── core/
│
├── memory/
│
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
├── setup.py
└── README.md
🏗️ How JARVIS Works
                USER
                  │
                  ▼
        ┌──────────────────┐
        │   JARVIS INPUT   │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │   AI / PLANNER   │
        └────────┬─────────┘
                 │
        ┌────────┼─────────┐
        ▼        ▼         ▼
   Computer   Browser   Developer
   Control   Automation    Tools
        │        │         │
        └────────┼─────────┘
                 ▼
        ┌──────────────────┐
        │     RESPONSE     │
        └──────────────────┘
🤝 Contributing

Contributions are welcome.

Fork the repository:

https://github.com/brandon-wrld/jarvis-brandon

Create a feature branch:

git checkout -b feature/my-feature

Make your changes, test them, and submit a pull request.

🛣️ Roadmap
 Improved wake-word detection
 Better long-term memory
 More AI providers
 Improved browser automation
 More computer automation
 Linux desktop support
 macOS support
 Plugin architecture
 Voice-only mode
 Improved GUI
 First-run setup wizard
 One-click Windows installer
 Automatic updates
 Standalone .exe application
👨‍💻 Author
Brandon Maina

GitHub:

https://github.com/brandon-wrld

Project:

https://github.com/brandon-wrld/jarvis-brandon

⭐ Support the Project

If you find JARVIS useful:

⭐ Star the repository
🍴 Fork the project
🐛 Report bugs
💡 Suggest features
🤝 Contribute improvements

🤖 JARVIS

Think. Understand. Automate. Execute.

Built with Python + AI.
