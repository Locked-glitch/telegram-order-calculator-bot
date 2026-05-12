from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "8749691441:AAH7SbWP1YC8_kwXr42emE1vVvt1sZAdn3k"


def send_message(chat_id, reply):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url, json={
        "chat_id": chat_id,
        "text": reply
    })


@app.route("/", methods=["POST"])
def risk_management():

    data = request.get_json()

    if "message" not in data:
        return "ok"

    message = data["message"]

    chat_id = message["chat"]["id"]

    text = message.get("text", "")
    text = text.strip()

    user = message["from"]
    username = user.get("first_name", "Trader")

    parts = text.split()

    if text == "/start":

        reply = (
            f"📈 Welcome {username}!\n\n"
            f"I am your Trading Order Calculator Bot 🤖\n\n"
            f"Send your trade setup in this format:\n\n"
            f"Entry TP% SL%\n\n"
            f"Example:\n"
            f"100 20 10\n\n"
            f"Meaning:\n"
            f"• Entry = 100\n"
            f"• Take Profit = 20%\n"
            f"• Stop Loss = 10%\n\n"
            f"⚡ Send your setup anytime to calculate instantly."
        )

        send_message(chat_id, reply)

    else:

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
                f"👤 Trader: {username}\n\n"
                f"💰 Entry Price:\n"
                f"{ent:.4f}\n\n"
                f"🎯 Take Profit:\n"
                f"{take:.4f}\n\n"
                f"🛑 Stop Loss:\n"
                f"{stop:.4f}\n\n"
                f"✅ Calculation completed successfully."
            )

            send_message(chat_id, reply)

        except ValueError:

            reply = (
                f"⚠️ Invalid trade format.\n\n"
                f"Please use this format:\n\n"
                f"Entry TP% SL%\n\n"
                f"Example:\n"
                f"100 20 10"
            )

            send_message(chat_id, reply)

    return "ok"


app.run(host="0.0.0.0", port=5000)
