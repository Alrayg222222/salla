from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

# جلب التوكن و Chat ID من متغيرات البيئة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# دالة لإرسال الرسالة إلى تيليجرام
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

# المسار الذي يتلقى بيانات Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # تنسيق الرسالة بشكل مناسب
    message = "<b>📦 Webhook من سلة:</b>\n\n"
    message += json.dumps(data, indent=2, ensure_ascii=False)
    
    # إرسال الرسالة لتيليجرام
    send_to_telegram(message)
    
    return "تم الاستلام", 200

# تشغيل التطبيق
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
