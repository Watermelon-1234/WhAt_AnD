# WhAt_AnD (What are you doing right now?)

**WhAt_AnD** is a minimalist, cross-platform focus tracking tool. It periodically pops up an always-on-top window to ask, "What are you doing right now?" By creating these micro-interruptions, it helps you pull your attention back, avoid distractions, and keep a log of your work trajectory.

## ✨ Features
* **Periodic Reminders**: Customizable popup intervals (seconds/minutes/hours) to check your current status.
* **Always-on-Top Focus Widget**: After entering your task, the prompt transforms into a borderless, always-on-top mini window to constantly remind you of your current focus.
* **Cross-Desktop Penetration (macOS)**: The mini window seamlessly follows you across all virtual desktops (Spaces) and full-screen applications.
* **History Logging**: Automatically saves each session's work log in JSON format for easy review.
* **Theming**: Built-in Dark Mode and Light Mode.

## 🚀 Requirements & Installation
1. Ensure you have Python 3.8 or higher installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## 💻 Supported Platforms
* **Windows**
* **macOS** (Requires `pyobjc` to support seamless transitioning across macOS Spaces, which is already configured in the `requirements.txt`).
* **Linux**
