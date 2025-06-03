from flask import Flask, redirect, request, jsonify
import json
import datetime
import random

app = Flask(__name__)

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

@app.route("/track")
def track():
    uid = request.args.get("uid")
    ref = request.args.get("ref")
    users = load_users()

    if uid not in users:
        users[uid] = {
            "points": 0,
            "last_reset": now_time().strftime("%Y-%m-%d %H:%M:%S"),
            "tasks_done": [],
            "ref": ref if ref else "",
            "ad_clicks": 0,
            "ref_bonus_given": False
        }

    user = users[uid]

    if time_diff_in_hours(user["last_reset"]) >= 6:
        user["last_reset"] = now_time().strftime("%Y-%m-%d %H:%M:%S")
        user["tasks_done"] = []

    if len(user["tasks_done"]) < 30:
        task_id = len(user["tasks_done"]) + 1
        user["tasks_done"].append(task_id)
        user["points"] += 2
        user["ad_clicks"] += 1

        # Referral bonus
        if user["ref"] and not user["ref_bonus_given"] and user["ad_clicks"] >= 1:
            referrer = users.get(user["ref"])
            if referrer:
                referrer["points"] += 5
                user["ref_bonus_given"] = True

    users[uid] = user
    save_users(users)
    return "✅ Task recorded!"

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

@app.route("/bonus")
def bonus():
    uid = request.args.get("uid")
    if not uid:
        return "❌ Missing UID"

    users = load_users()
    user = users.get(uid, {
        "points": 0,
        "clicks": 0,
        "task_progress": {},
        "last_reset_time": str(now_time()),
        "last_bonus_date": "",
        "ref": None
    })

    today = now_time().strftime("%Y-%m-%d")
    if user["last_bonus_date"] == today:
        return "🎁 Bonus already claimed today!"

    bonus = random.randint(1, 2)
    user["points"] += bonus
    user["last_bonus_date"] = today

    users[uid] = user
    save_users(users)
    return f"🎁 You received {bonus} bonus points today!"

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

@app.route("/referral", methods=["POST"])
def referral():
    data = request.get_json()
    uid = data.get("uid")
    referrer_code = data.get("referrer")

    if not uid or not referrer_code:
        return jsonify({"error": "Missing data"}), 400

    try:
        with open("referrals.json", "r") as f:
            referrals = json.load(f)
    except:
        referrals = {}

    if uid in referrals:
        return jsonify({"message": "Already referred"}), 200

    referrals[uid] = referrer_code
    with open("referrals.json", "w") as f:
        json.dump(referrals, f)

    try:
        with open("points.json", "r") as f:
            points = json.load(f)
    except:
        points = {}

    points[referrer_code] = points.get(referrer_code, 0) + 5

    with open("points.json", "w") as f:
        json.dump(points, f)

    return jsonify({"message": "Referral recorded & rewarded"}), 200

if __name__ == "__main__":
    app.run()
