from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    message = "<b>📦 Webhook من سلة:</b>\n\n"
    message += json.dumps(data, indent=2, ensure_ascii=False)
    send_to_telegram(message)
    return "تم الاستلام", 200

if __name__ == '__main__':
    app.run()
