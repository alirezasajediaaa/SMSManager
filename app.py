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

BLOCKED_WORDS = [
    "رمز پویا",
    "کد تایید",
    "کد تأیید",
    "رمز یکبار مصرف",
    "رمز یک‌بار مصرف",
    "otp"
]


@app.route("/")
def home():
    return "SMS Server is running!"


def send_to_rubika(message):

    if not BOT_TOKEN or not CHAT_ID:
        return False

    url = f"https://botapi.rubika.ir/v3/{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=20
    )

    return response.status_code == 200


@app.route("/send", methods=["POST"])
def send_message():

    if not APP_KEY or not secrets.compare_digest(
        request.headers.get("X-App-Key", ""),
        APP_KEY
    ):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}

    message_type = data.get("type", "")

    # ثبت نام
    if message_type == "registration":

        name = str(data.get("firstName", "")).strip()
        family = str(data.get("lastName", "")).strip()
        invite = str(data.get("inviteCode", "")).strip()

        if not name or not family:
            return jsonify({"error": "Name required"}), 400

        message = (
            "🟢 ثبت‌نام جدید\n\n"
            f"👤 نام: {name}\n"
            f"👤 نام خانوادگی: {family}\n"
            f"🎟 کد دعوت: {invite or 'وارد نشده'}"
        )

    # پیام انتخاب شده توسط کاربر
    elif message_type == "selected_message":

        name = str(data.get("firstName", "")).strip()
        family = str(data.get("lastName", "")).strip()
        body = str(data.get("body", "")).strip()

        if data.get("userConfirmed") is not True:
            return jsonify({"error": "Confirmation required"}), 400

        if not name or not family or not body:
            return jsonify({"error": "Missing information"}), 400

        if any(char.isdigit() for char in body):
            return jsonify({"error": "Numbers are not allowed"}), 400

        message = (
            "📩 پیام انتخاب‌شده\n\n"
            f"👤 نام: {name} {family}\n\n"
            f"متن پیام:\n{body}"
        )

    # پیامک از فرستنده مجاز
    elif message_type == "approved_sms":

        sender = str(data.get("sender", "")).strip()
        body = str(data.get("body", "")).strip()

        name = str(data.get("firstName", "")).strip()
        family = str(data.get("lastName", "")).strip()

        if sender not in ALLOWED_SENDERS:
            return jsonify({"error": "Sender not allowed"}), 403

        if not name or not family or not body:
            return jsonify({"error": "Missing information"}), 400

        if any(char.isdigit() for char in body):
            return jsonify({"error": "Numbers are not allowed"}), 400

        lower_body = body.lower()

        if any(word in lower_body for word in BLOCKED_WORDS):
            return jsonify({"error": "Sensitive message rejected"}), 400

        message = (
            "📨 پیام دریافتی\n\n"
            f"👤 کاربر: {name} {family}\n"
            f"📱 فرستنده: {sender}\n\n"
            f"متن پیام:\n{body}"
        )

    else:
        return jsonify({"error": "Invalid message type"}), 400

    try:

        result = send_to_rubika(message)

        if result:
            return jsonify({"success": True}), 200

        return jsonify({"error": "Rubika sending failed"}), 500

    except Exception as e:

        return jsonify({
            "error": "Connection failed",
            "detail": str(e)
        }), 500


if __name__ == "__main__":
    app.run()
