import os
import logging
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CASHFREE_CLIENT_ID = os.getenv("CASHFREE_CLIENT_ID")
CASHFREE_CLIENT_SECRET = os.getenv("CASHFREE_CLIENT_SECRET")
CASHFREE_BASE_URL = "https://sandbox.cashfree.com/pg"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("bot")

user_payment_status = {}

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)
    logger.debug(f"Telegram response: {response.status_code} - {response.text}")
    return response

def create_cashfree_order(user_id):
    headers = {
        "x-api-version": "2022-09-01",
        "Content-Type": "application/json",
        "x-client-id": CASHFREE_CLIENT_ID,
        "x-client-secret": CASHFREE_CLIENT_SECRET
    }
    order_id = f"kidslogger_{user_id}_{int(time.time())}"
    data = {
        "order_id": order_id,
        "order_amount": 300.00,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(user_id),
            "customer_email": "demo@example.com",
            "customer_phone": "9999999999"
        },
        "order_meta": {
            "return_url": "https://tellogs.koyeb.app/paid-success",
            "notify_url": "https://tellogs.koyeb.app/cashfree-webhook"
        }
    }
    response = requests.post(f"{CASHFREE_BASE_URL}/orders", json=data, headers=headers)
    logger.debug(f"Cashfree Response: {response.status_code} - {response.text}")
    if response.status_code == 200:
        return response.json()
    return None

@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    data = request.json
    logger.debug(f"Telegram data: {data}")
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text.startswith("/start"):
            send_message(chat_id, "👋 Welcome to the keylogger APK Generator Bot!\n\nDeveloped by https://www.instagram.com/cyber.naveen.info\n\n🛡 Disclaimer: This is for educational/parental use only.\n\nUse /pay to proceed or /request_apk after payment.")

        elif text.startswith("/pay"):
            cf_data = create_cashfree_order(chat_id)
            if cf_data:
                payment_url = cf_data.get("payments", {}).get("url")
                if payment_url:
                    user_payment_status[str(chat_id)] = "pending"
                    send_message(chat_id, f"💰 Please complete the payment using this link: {payment_url}")
                else:
                    send_message(chat_id, "❌ Payment link could not be created. Try again later.")
            else:
                send_message(chat_id, "❌ Payment request failed. Please try again.")

        elif text.startswith("/request_apk"):
            if user_payment_status.get(str(chat_id)) == "paid":
                send_message(chat_id, "✅ Payment verified! Your APK will be generated and sent shortly.")
                # trigger GitHub Action or other build step
            else:
                send_message(chat_id, "⚠️ Payment not verified yet. Please use /pay to complete the payment.")

    return jsonify(success=True)

@app.route("/cashfree-webhook", methods=["POST"])
def cashfree_webhook():
    data = request.json
    logger.debug(f"Cashfree Webhook Data: {data}")
    order_id = data.get("order", {}).get("order_id")
    payment_status = data.get("payment", {}).get("payment_status")
    if order_id and payment_status == "SUCCESS":
        user_id = order_id.split("_")[1]
        user_payment_status[user_id] = "paid"
        send_message(user_id, "✅ Payment received! You can now use /request_apk to generate your APK.")
    return jsonify(success=True)

@app.route("/")
def index():
    return "Bot is running."

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

