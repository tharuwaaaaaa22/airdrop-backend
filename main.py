
from flask import Flask, redirect, request, jsonify
from flask_cors import CORS
import json
import datetime
import random
import requests

app = Flask(__name__)
CORS(app)

BOT_TOKEN = "7572938961:AAGscfeGVd3sMqwPonvAaqaWE2n2xukT8Hc"
ADMIN_ID = "1081808918"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": ADMIN_ID, "text": text}
    requests.post(url, json=data)

def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=2)

def now_time():
    return datetime.datetime.now()

def time_diff_in_hours(past):
    try:
        last = datetime.datetime.strptime(past, "%Y-%m-%d %H:%M:%S")
        return (now_time() - last).total_seconds() / 3600
    except:
        return 100

@app.route("/")
def home():
    return "✅ Airdrop Backend Running!"

@app.route("/points")
def points():
    uid = request.args.get("uid")
    if not uid:
        return "❌ Missing UID"
    users = load_users()
    user = users.get(uid)
    if not user:
        return "User not found"
    return f"{user['points']}"

@app.route("/withdraw", methods=["POST"])
def withdraw():
    data = request.get_json()
    uid = data.get("uid")
    address = data.get("address")
    amount = data.get("amount")

    if not all([uid, address, amount]):
        return {"status": "error", "message": "Missing data"}, 400

    users = load_users()
    withdraws = load_withdraws()
    user = users.get(uid)

    if not user:
        return {"status": "error", "message": "User not found"}, 404

    required_points = {1: 1000, 3: 3000, 5: 5000}.get(amount)
    if not required_points:
        return {"status": "error", "message": "Invalid amount"}, 400

    if user["points"] < required_points:
        return {"status": "error", "message": "Not enough points"}, 403

    user["points"] -= required_points
    withdraws.append({
        "uid": uid,
        "amount": amount,
        "address": address,
        "time": now_time().strftime("%Y-%m-%d %H:%M:%S")
    })

    save_users(users)
    save_withdraws(withdraws)

    # Send Telegram message
    message = f"🚨 New Withdraw Request\n👤 User: {uid}\n💵 Amount: ${amount}\n🏦 Binance ID: {address}"
    send_telegram_message(message)

    return {"status": "success"}

@app.route("/admin/withdraws")
def admin_withdraws():
    try:
        with open("withdraws.json", "r") as f:
            return f.read(), 200, {'Content-Type': 'application/json'}
    except:
        return "[]"

def load_withdraws():
    try:
        with open("withdraws.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_withdraws(data):
    with open("withdraws.json", "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
