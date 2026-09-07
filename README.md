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

make look presentable

Absolutely. I’d make it look much more like a professional open-source project README instead of a long installation document. Here is a cleaner, more polished version you can paste directly into GitHub.

# 🤖 JARVIS

<p align="center">
  <strong>Your Personal AI Assistant</strong>
</p>

<p align="center">
  Think • Understand • Automate • Execute
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)
![AI](https://img.shields.io/badge/AI-Powered-purple?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-success?style=for-the-badge&logo=windows)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</p>

---

## 🧠 What is JARVIS?

**JARVIS** is a Python-powered personal AI assistant designed to help you interact with your computer, automate tasks, search the web, work with files, control your browser, and communicate using voice.

JARVIS combines **AI intelligence + voice interaction + computer automation + browser automation** into one assistant.

> ⚡ Run it locally on your computer for the complete JARVIS experience.

---

# ✨ Features

| Feature | Description |
|---|---|
| 🧠 **AI Assistant** | Natural-language conversations and intelligent responses |
| 🎙️ **Voice Control** | Voice input and text-to-speech |
| 🖥️ **Desktop Control** | Interact with your computer |
| 🖱️ **Mouse & Keyboard** | Automate mouse and keyboard actions |
| 🌐 **Browser Automation** | Control browsers using Playwright |
| 🔎 **Web Search** | Search and retrieve online information |
| 📁 **File Processing** | Work with documents and files |
| 👨‍💻 **Developer Assistant** | Coding and development assistance |
| 📺 **YouTube Tools** | YouTube-related automation |
| 🔔 **Reminders** | Create and manage reminders |
| 🧠 **Memory** | Store and manage assistant information |
| 🔐 **AI Providers** | Gemini and OpenRouter support |

---

# 🖥️ Recommended Platform

### 🪟 Windows

Windows is currently the **recommended platform** for running the complete version of JARVIS.

This allows JARVIS to interact with your actual:

```text
🎤 Microphone
🔊 Speakers
🖥️ Screen
🖱️ Mouse
⌨️ Keyboard
🪟 Windows Applications
🌐 Browser
📥 Getting Started
⚠️ New Users — Read This First

You must download the ZIP from GitHub and extract it before running JARVIS.

JARVIS is currently distributed as a Python project and is not yet a standalone .exe application.

1️⃣ Open the Repository

Visit:

👉 https://github.com/brandon-wrld/jarvis-brandon

2️⃣ Download JARVIS

On the GitHub page:

Code
  ↓
Download ZIP

The ZIP will normally be saved inside your:

Downloads/

folder.

You should see something similar to:

jarvis-brandon-main.zip
3️⃣ Extract the ZIP

Right-click the ZIP:

jarvis-brandon-main.zip

Select:

Extract All...

Extract it somewhere convenient, such as your:

Desktop/

You should now have:

Desktop/
└── jarvis-brandon-main/
🚨 Important

Do not run JARVIS directly from inside the ZIP.

You must:

Download
   ↓
Extract
   ↓
Open the extracted folder
   ↓
Install
   ↓
Configure
   ↓
Run
⚙️ Installation
Requirements

Before installing, make sure you have:

🪟 Windows 10 or Windows 11
🐍 Python 3.13
🌐 Internet connection
🎤 Working microphone
🔊 Speakers or headphones
1️⃣ Open the JARVIS Folder

For example:

C:\Users\YourName\Desktop\jarvis-brandon-main

Make sure you can see:

main.py
requirements.txt
setup.py
actions/
agent/
config/
core/
memory/
2️⃣ Open PowerShell

Open the JARVIS folder in File Explorer.

Click the address bar and type:

powershell

Press Enter.

Check your location:

dir

You should see:

main.py
requirements.txt
3️⃣ Create a Virtual Environment
py -3.13 -m venv .venv
4️⃣ Activate the Environment
.\.venv\Scripts\Activate.ps1

You should see:

(.venv) PS C:\Users\YourName\Desktop\jarvis-brandon-main>
PowerShell Execution Policy Error?

If you see:

running scripts is disabled

run:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Then:

.\.venv\Scripts\Activate.ps1
📦 Install Dependencies

Upgrade pip:

python -m pip install --upgrade pip setuptools wheel

Install JARVIS dependencies:

pip install -r requirements.txt

Then install the browser required by Playwright:

python -m playwright install chromium
🔑 API Configuration

JARVIS requires an AI API key.

Inside the project you will find:

.env.example

Create a copy named:

.env

Your project should look like:

jarvis-brandon-main/
│
├── .env
├── .env.example
├── main.py
└── ...

Open .env and add your own keys:

GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

Replace the placeholders with your actual API keys.

🔐 Security
🚨 Never upload your API keys to GitHub.

Keep these files private:

.env
config/api_keys.json

Never post API keys on:

❌ GitHub
❌ WhatsApp
❌ Discord
❌ Screenshots
❌ Social media
❌ Public repositories

Every user should use their own API keys.

If you accidentally expose a key, revoke it immediately and generate a new one.

▶️ Launch JARVIS

Make sure your virtual environment is active:

.\.venv\Scripts\Activate.ps1

Then:

python main.py

🚀 JARVIS should now start.

🎤 Test Your Microphone

Before using voice features, run:

python -c "import sounddevice as sd; print(sd.query_devices())"

Your microphone should appear in the device list.

If it doesn't, check:

Windows Settings
      ↓
System
      ↓
Sound
      ↓
Input

Make sure the correct microphone is selected.

🖱️ Test Computer Control

JARVIS uses PyAutoGUI for computer interaction.

Run:

python -c "import pyautogui; print(pyautogui.size())"

A successful result will look similar to:

Size(width=1920, height=1080)
🌐 Browser Automation

JARVIS uses Playwright for browser automation.

If you receive a Chromium/browser error, run:

python -m playwright install chromium

Then start JARVIS again:

python main.py
☁️ GitHub Codespaces
⚠️ Why Codespaces Isn't Recommended for Full JARVIS

GitHub Codespaces is excellent for developing JARVIS, but it is not designed to give a cloud machine direct control over your physical computer.

Why?

Codespaces runs your project on a:

Remote Linux computer in the cloud.

Your physical computer is somewhere else.

For example:

        YOUR COMPUTER
┌──────────────────────────┐
│ 🖥️ Real Screen           │
│ 🎤 Microphone            │
│ 🔊 Speakers              │
│ 🖱️ Mouse                 │
│ ⌨️ Keyboard              │
│ 🪟 Windows Apps          │
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
│ Virtual Environment      │
└──────────────────────────┘

When you run:

python main.py

inside Codespaces, JARVIS runs on the remote Linux machine.

It does not automatically get access to your physical:

🎤 Microphone
🔊 Speakers
🖥️ Windows Screen
🖱️ Mouse
⌨️ Keyboard
📷 Webcam
🪟 Windows Applications
❓ What About DISPLAY and XAUTHORITY?

You may see solutions using:

DISPLAY=:99
XAUTHORITY=/tmp/.Xauthority

These settings can create or configure a virtual display inside the Codespace.

They do not connect that virtual display to your physical Windows screen.

For example:

DISPLAY=:99

means:

Use display :99 inside the remote Linux environment.

It does not mean:

Control the Windows screen in front of the user.

The same applies to audio.

Installing PortAudio or other Linux audio packages can make audio devices available inside the remote environment, but it does not automatically connect JARVIS to the microphone and speakers physically connected to your Windows computer.

✅ The solution

For the complete JARVIS experience:

Download → Extract → Install → Run locally on Windows.

Use Codespaces primarily for development.

🏗️ Architecture
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
├── core/
├── memory/
│
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
├── setup.py
└── README.md
🛠️ Troubleshooting
❌ Python not recognized

Check:

py --version

Python 3.13 is recommended.

❌ ModuleNotFoundError

Activate your virtual environment:

.\.venv\Scripts\Activate.ps1

Then reinstall:

pip install -r requirements.txt
❌ Playwright error

Run:

python -m playwright install chromium
❌ Microphone not detected

Check:

Windows Settings
→ System
→ Sound
→ Input

Then:

python -c "import sounddevice as sd; print(sd.query_devices())"
❌ JARVIS won't start

Run:

python main.py

Read the error shown in PowerShell.

When asking for support, provide the complete error/traceback.

🛣️ Roadmap
Current
 AI conversations
 Computer automation
 Browser automation
 Web search
 Voice capabilities
 File processing
 Developer tools
 Memory system
 Gemini support
 OpenRouter support
Future
 Advanced wake-word detection
 Improved long-term memory
 More AI providers
 Advanced browser automation
 Plugin architecture
 Improved GUI
 Linux desktop support
 macOS support
 First-run setup wizard
 Automatic updates
 One-click Windows installer
 Standalone .exe application
🤝 Contributing

Contributions are welcome!

Fork the repository
git clone https://github.com/brandon-wrld/jarvis-brandon.git

Create a branch:

git checkout -b feature/my-feature

Make your changes, test them, and submit a pull request.

🐛 Issues & Support

Found a bug?

Open an issue on GitHub:

👉 https://github.com/brandon-wrld/jarvis-brandon/issues

When reporting an issue, include:

Operating system
Python version
JARVIS version/commit
Complete error message
Steps to reproduce the problem

Never include your API keys.

⭐ Support JARVIS

If you like the project, consider supporting it:

⭐ Star the repository

🍴 Fork the project

🐛 Report bugs

💡 Suggest features

🤝 Contribute

👨‍💻 Author
Brandon Maina

GitHub:

👉 https://github.com/brandon-wrld

Project:

👉 https://github.com/brandon-wrld/jarvis-brandon

<p align="center">
🤖 JARVIS
Think. Understand. Automate. Execute.

Built with Python + AI

⭐ Star the project if you find it useful!

</p> ```
