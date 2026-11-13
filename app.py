import os
import secrets
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
APP_KEY = os.environ.get("APP_KEY")

ALLOWED_SENDERS = {
    "09999987641",
    "09961257630"
}


@app.route("/")
def home():
    return "SMS Forwarder Server is Running!"


@app.route("/send", methods=["POST"])
def send_sms():

    if not APP_KEY or not secrets.compare_digest(
        request.headers.get("X-App-Key", ""),
        APP_KEY
    ):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}

    sender = str(data.get("sender", "")).strip()
    body = str(data.get("body", "")).strip()

    if sender not in ALLOWED_SENDERS:
        return jsonify({"error": "Sender not allowed"}), 403

    if not body:
        return jsonify({"error": "Empty message"}), 400

    message = (
        "📩 پیامک جدید\n\n"
        f"📱 شماره فرستنده: {sender}\n\n"
        f"📝 متن پیام:\n{body}"
    )

    try:
        url = f"https://botapi.rubika.ir/v3/{BOT_TOKEN}/sendMessage"

        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=20
        )

        if response.status_code == 200:
            return jsonify({"success": True}), 200

        return jsonify({"error": "Rubika sending failed"}), 502

    except requests.RequestException:
        return jsonify({"error": "Connection failed"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
