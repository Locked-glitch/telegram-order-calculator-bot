from flask import Flask, request
import requests
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
TOKEN = "8749691441:AAH7SbWP1YC8_kwXr42emE1vVvt1sZAdn3k"

DB = "bot.db"

# ---------------- TELEGRAM ----------------
def send_message(chat_id, reply):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": reply})


# ---------------- DB INIT ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        status TEXT,
        trial_end TEXT,
        last_reset TEXT,
        usage_count INTEGER
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- USER HELPERS ----------------
def get_user(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user


def create_user(user_id, username):
    now = datetime.now()

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO users (user_id, username, status, trial_end, last_reset, usage_count)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        username,
        "trial",
        (now + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
        now.strftime("%Y-%m-%d"),
        0
    ))

    conn.commit()
    conn.close()


def update_user(user):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    UPDATE users
    SET status=?, trial_end=?, last_reset=?, usage_count=?
    WHERE user_id=?
    """, (
        user["status"],
        user["trial_end"],
        user["last_reset"],
        user["usage_count"],
        user["user_id"]
    ))

    conn.commit()
    conn.close()


# ---------------- ACCESS CONTROL ----------------
def check_access(user):

    now = datetime.now().strftime("%Y-%m-%d")

    # reset daily usage
    if user["last_reset"] != now:
        user["usage_count"] = 0
        user["last_reset"] = now

    # free limit = 2/day
    if user["status"] == "free" and user["usage_count"] >= 2:
        return "limit"

    # trial expiry
    if user["status"] == "trial":
        if datetime.now() > datetime.strptime(user["trial_end"], "%Y-%m-%d %H:%M:%S"):
            user["status"] = "free"

    return "ok"


# ---------------- WEBHOOK ----------------
@app.route(f"/{TOKEN}", methods=["POST"])
def risk_management():

    data = request.get_json()

    if "message" not in data:
        return "ok"

    message = data["message"]

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    user = message["from"]
    username = user.get("first_name", "Trader")
    user_id = user["id"]

    parts = text.split()

    # ---------------- GET OR CREATE USER ----------------
    db_user = get_user(user_id)

    if not db_user:
        create_user(user_id, username)
        db_user = get_user(user_id)

    user_obj = {
        "user_id": db_user[0],
        "username": db_user[1],
        "status": db_user[2],
        "trial_end": db_user[3],
        "last_reset": db_user[4],
        "usage_count": db_user[5]
    }

    access = check_access(user_obj)

    # ---------------- START ----------------
    if text == "/start":

        reply = (
            f"📈 Welcome {username}!\n\n"
            f"🔥 You got 3 DAYS FREE TRIAL\n"
            f"⚡ After that: 2 free uses/day\n\n"
            f"Send:\n100 20 10"
        )

        send_message(chat_id, reply)
        return "ok"

    # ---------------- BLOCK USERS ----------------
    if access == "limit":
        send_message(chat_id,
            "🚫 Daily limit reached (2 requests/day).\n"
            "💰 Upgrade to Premium for unlimited access.")
        return "ok"

    # ---------------- INPUT ----------------
    try:

        if len(parts) != 3:
            raise ValueError

        ent = float(parts[0])
        tp = float(parts[1])
        sl = float(parts[2])

        stop = ent - (sl / 100 * ent)
        take = ent + (tp / 100 * ent)

        reply = (
            f"📊 Trade Calculation\n\n"
            f"👤 {username}\n"
            f"📈 Entry: {ent:.4f}\n"
            f"🎯 TP: {take:.4f}\n"
            f"🛑 SL: {stop:.4f}\n\n"
            f"⚡ Status: {user_obj['status'].upper()}"
        )

        send_message(chat_id, reply)

        # update usage
        user_obj["usage_count"] += 1
        update_user(user_obj)

    except ValueError:

        send_message(chat_id,
            "⚠️ Invalid format\nUse:\n100 20 10")

    return "ok"


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
