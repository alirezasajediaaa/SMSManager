import os
import secrets
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
APP_KEY = os.environ.get("APP_KEY")


@app.route("/")
def home():
    return "SMS Server is running!"


@app.route("/send", methods=["POST"])
def send_message():

    if not APP_KEY or not secrets.compare_digest(
        request.headers.get("X-App-Key", ""),
        APP_KEY
    ):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}

    message_type = data.get("type", "")

    if message_type == "registration":

        name = str(data.get("firstName", "")).strip()
        family = str(data.get("lastName", "")).strip()
        invite = str(data.get("inviteCode", "")).strip()

        if not name or not family:
            return jsonify({"error": "Name required"}), 400

        message = (
            "🟢 ثبت‌نام جدید\n\n"
            "👤 نام: " + name + "\n"
            "👤 نام خانوادگی: " + family + "\n"
            "🎟 کد دعوت: " +
            (invite if invite else "وارد نشده")
        )

    elif message_type == "selected_message":

        name = str(data.get("firstName", "")).strip()
        family = str(data.get("lastName", "")).strip()
        body = str(data.get("body", "")).strip()

        if not name or not family or not body:
            return jsonify({"error": "Missing data"}), 400

        if any(char.isdigit() for char in body):
            return jsonify({
                "error": "Messages containing numbers are not accepted"
            }), 400

        blocked_words = [
            "رمز پویا",
            "کد تایید",
            "کد تأیید",
            "رمز یکبار مصرف",
            "رمز یک‌بار مصرف",
            "otp",
            "رمز دوم",
            "cvv",
            "cvv2",
            "شماره کارت"
        ]

        lower_body = body.lower()

        if any(word in lower_body for word in blocked_words):
            return jsonify({"error": "Sensitive message"}), 400

        message = (
            "📩 پیام انتخاب‌شده\n\n"
            "👤 نام: " + name + "\n"
            "👤 نام خانوادگی: " + family + "\n\n"
            "متن پیام:\n" + body
        )

    else:
        return jsonify({"error": "Invalid type"}), 400

    if not BOT_TOKEN or not CHAT_ID:
        return jsonify({"error": "Bot settings missing"}), 500

    url = f"https://botapi.rubika.ir/v3/{BOT_TOKEN}/sendMessage"

    try:

        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=20
        )

        return jsonify(response.json()), response.status_code

    except Exception:
        return jsonify({"error": "Connection failed"}), 500


if __name__ == "__main__":
    app.run()
