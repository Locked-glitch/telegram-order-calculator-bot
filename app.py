from flask import Flask, request
import requests
app = Flask(__name__)
TOKEN = "token"
def send_message(chat_id, reply):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": reply
    })
@app.route("/",methods=["POST"])
def risk_management():
    data = request.get_json()
    message = data["message"]
    if "message" not in data:
        return"ok"
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    text = text.strip()
    user = message["from"]
    username = user.get("first_name", "user")
    parts = text.split()
    if text == "/start":
        reply = (f"Welcome {username}, I am your Order Calculator Bot !!\n"
                 f"Please enter your orders as follows:\n100 20 10")
        send_message(chat_id, reply)
    else:
        try:
            ent = float(parts[0])
            tp = float(parts[1])
            sl = float(parts[2])
            stop = ent - (sl / 100 * ent)
            take = ent + (tp / 100 * ent)
            reply = (f'Hey {username}\nYour TP is : {take:.4f}\n'
                     f'Your SL is : {stop:.4f}')
            send_message(chat_id, reply)
        except ValueError:
            reply = "Invalid Command🚫"
            send_message(chat_id, reply)
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
