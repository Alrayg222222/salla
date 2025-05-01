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
    
    # تفاصيل المنتجات مع عدد مرات الشراء ومجموع السعر
    message += "<b>تفاصيل المنتجات:</b>\n"
    total_products_amount = 0
    for item in data['data']['items']:
        product_name = item['name']
        quantity = item['quantity']
        price = item['total']['amount']
        total_product_price = price * quantity  # حساب مجموع السعر للمنتج بناءً على الكمية
        message += f"- <b>{product_name}</b> x{quantity}\n"
        message += f"سعر المنتج: <b>{price} {item['total']['currency']}</b>\n"
        message += f"مجموع السعر: <b>{total_product_price:.2f} {item['total']['currency']}</b>\n"
        
        total_products_amount += total_product_price  # جمع مجموع أسعار المنتجات
    
    # عرض مجموع المنتجات
    message += f"\n<b>مجموع المنتجات:</b>\n"
    message += f"المجموع: <b>{total_products_amount:.2f} {data['data']['total']['currency']}</b>\n"
    
    # إجمالي الطلب
    total_amount = data['data']['total']['amount']
    message += "\n<b>إجمالي الطلب:</b>\n"
    message += f"المجموع: <b>{total_amount:.2f} {data['data']['total']['currency']}</b>\n"
    
    # تحديث المجموع الإجمالي
    update_total_collected(total_amount)
    
    # إضافة 5 أسطر فارغة بين المجموع الإجمالي والبيانات السابقة
    message += "\n\n\n\n\n"  # 5 أسطر فارغة

    # عرض المجموع الإجمالي للمبالغ التي تم جمعها في آخر 24 ساعة
    message += "<b>المجموع الإجمالي خلال آخر 24 ساعة:</b>\n"
    message += f"المجموع: <b>{total_collected:.2f} {data['data']['total']['currency']}</b>\n"
    
    # إرسال الرسالة إلى تيليجرام
    send_to_telegram(message)
    
    return "تم الاستلام", 200

# تشغيل التطبيق
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
