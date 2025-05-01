from flask import Flask, request
import requests
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# جلب التوكن و Chat ID من متغيرات البيئة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# متغير لتخزين المجموع الإجمالي
total_collected = 0
last_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# دالة لإرسال الرسالة إلى تيليجرام
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

# دالة لتحديث المجموع الإجمالي
def update_total_collected(amount):
    global total_collected, last_reset_time
    current_time = datetime.now()
    
    # إذا مر 24 ساعة من آخر تحديث (12:00 صباحًا)
    if current_time >= last_reset_time + timedelta(days=1):
        total_collected = 0  # إعادة تعيين المجموع
        last_reset_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)  # تعيين بداية اليوم الجديد
    
    total_collected += amount  # إضافة المبلغ الجديد إلى المجموع

# المسار الذي يتلقى بيانات Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # تنسيق الرسالة بشكل مناسب
    message = "<b>📦 Webhook من سلة:</b>\n\n"
    
    # تفاصيل الفاتورة
    message += "<b>تفاصيل الفاتورة:</b>\n"
    message += f"رقم الفاتورة: <code>{data['data']['invoice_number']}</code>\n"
    message += f"نوع الفاتورة: <i>{data['data']['type']}</i>\n"
    message += f"تاريخ الفاتورة: <i>{data['data']['date']}</i>\n"
    
    # تفاصيل العميل
    customer = data['data']['customer']
    message += "\n<b>بيانات العميل:</b>\n"
    message += f"الاسم: <i>{customer['first_name']} {customer['last_name']}</i>\n"
    message += f"رقم الجوال: <i>{customer['mobile']}</i>\n"
    message += f"البريد الإلكتروني: <i>{customer['email']}</i>\n"
    message += f"العنوان: <i>{customer['address']['street_name']}، {customer['address']['city']}</i>\n"
    
    # تفاصيل الطلب
    message += "\n<b>تفاصيل الطلب:</b>\n"
    for item in data['data']['items']:
        message += f"- <b>{item['name']}</b> x{item['quantity']}\n"
        message += f"السعر: <b>{item['total']['amount']} {item['total']['currency']}</b>\n"
    
    # إجمالي الطلب
    total_amount = data['data']['total']['amount']
    message += "\n<b>إجمالي الطلب:</b>\n"
    message += f"المجموع: <b>{total_amount} {data['data']['total']['currency']}</b>\n"
    
    # تحديث المجموع الإجمالي
    update_total_collected(total_amount)
    
    # عرض المجموع الإجمالي للمبالغ التي تم جمعها في آخر 24 ساعة
    message += "\n<b>المجموع الإجمالي خلال آخر 24 ساعة:</b>\n"
    message += f"المجموع: <b>{total_collected} {data['data']['total']['currency']}</b>\n"
    
    # إرسال الرسالة إلى تيليجرام
    send_to_telegram(message)
    
    return "تم الاستلام", 200

# تشغيل التطبيق
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
