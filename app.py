import os
import re
import secrets
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
APP_KEY = os.environ.get("APP_KEY")

ALLOWED_SENDERS = {
    "09999987641",
    "09962157630",
    "+989999987641",
    "+989962157630"
}


def authorized():
    return (
        APP_KEY is not None
        and secrets.compare_digest(
            request.headers.get("X-App-Key", ""),
            APP_KEY
        )
    )


def send_to_rubika(message):
    if not BOT_TOKEN or not CHAT_ID:
        return False

    url = (
        "https://botapi.rubika.ir/v3/"
        + BOT_TOKEN
        + "/sendMessage"
    )

    response = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=20
    )

    response.raise_for_status()

    result = response.json()

    return result.get("status") == "OK"


@app.route("/", methods=["GET"])
def home():
    return "SMS Forwarder Server is Running!"


@app.route("/register", methods=["POST"])
def register():

    if not authorized():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}

    first_name = str(
        data.get("first_name", "")
    ).strip()

    last_name = str(
        data.get("last_name", "")
    ).strip()

    username = str(
        data.get("username", "")
    ).strip()

    if not first_name or not last_name:
        return jsonify({
            "error": "Name required"
        }), 400

    if len(first_name) > 50 or len(last_name) > 50:
        return jsonify({
            "error": "Name too long"
        }), 400

    if not re.fullmatch(r"[0-9]{4,20}", username):
        return jsonify({
            "error": "Invalid username"
        }), 400

    if not BOT_TOKEN or not CHAT_ID:
        return jsonify({
            "error": "Bot configuration missing"
        }), 500

    message = (
        "👤 ثبت‌نام کاربر جدید\n\n"
        f"نام: {first_name}\n"
        f"نام خانوادگی: {last_name}\n"
        f"شناسه کاربر: {username}"
    )

    try:
        if send_to_rubika(message):
            return jsonify({
                "success": True
            }), 200

        return jsonify({
            "error": "Rubika sending failed"
        }), 502

    except requests.RequestException:
        app.logger.exception("Rubika request failed")

        return jsonify({
            "error": "Connection failed"
        }), 502


@app.route("/send", methods=["POST"])
def send_sms():

    if not authorized():
        return jsonify({
            "error": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}

    sender = str(
        data.get("sender", "")
    ).strip()

    body = str(
        data.get("body", "")
    ).strip()

    if sender not in ALLOWED_SENDERS:
        return jsonify({
            "error": "Sender not allowed"
        }), 403

    if not body:
        return jsonify({
            "error": "Empty message"
        }), 400

    message = (
        "📩 پیامک جدید\n\n"
        f"شماره فرستنده: {sender}\n\n"
        f"متن پیام:\n{body}"
    )

    try:
        if send_to_rubika(message):
            return jsonify({
                "success": True
            }), 200

        return jsonify({
            "error": "Rubika sending failed"
        }), 502

    except requests.RequestException:
        app.logger.exception("SMS forwarding failed")

        return jsonify({
            "error": "Connection failed"
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
