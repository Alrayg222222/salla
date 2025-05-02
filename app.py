from flask import Flask, request
import requests
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# جلب التوكن و Chat ID من متغيرات البيئة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")  # Chat ID الأول
SECOND_CHAT_ID = os.environ.get("SECOND_CHAT_ID")  # Chat ID الثاني (الجديد)

# متغير لتخزين المجموع الإجمالي
total_collected = 0
last_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# قاموس لتخزين عدد مرات شراء كل منتج
product_purchase_count = {}

# دالة لإرسال الرسالة إلى تيليجرام
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # إرسال الرسالة إلى chat ID الأول
    payload_first = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload_first)
    
    # إرسال الرسالة إلى chat ID الثاني
    payload_second = {
        "chat_id": SECOND_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload_second)

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
    
    # تفاصيل المنتجات التي تم شراؤها في الطلب الحالي
    message += "<b>تفاصيل المنتجات:</b>\n"
    for item in data['data']['items']:
        product_name = item['name']
        quantity = item['quantity']
        price = item['total']['amount']
        
        # إضافة تفاصيل المنتج مع السعر والكمية
        message += f"- <b>{product_name}</b> x{quantity}\n"
        message += f"  السعر: <font color='green'><b>{price:.2f} {data['data']['total']['currency']}</b></font>\n"
    
    # مجموع المنتجات
    total_amount = data['data']['total']['amount']
    message += "\n<b>مجموع المنتجات:</b>\n"
    message += f"المجموع: <font color='blue'><b>{total_amount:.2f} {data['data']['total']['currency']}</b></font>\n"
    
    # إجمالي الطلب
    message += "\n<b>إجمالي الطلب:</b>\n"
    message += f"المجموع: <font color='blue'><b>{total_amount:.2f} {data['data']['total']['currency']}</b></font>\n"
    
    # تحديث عدد مرات شراء كل منتج
    for item in data['data']['items']:
        product_name = item['name']
        quantity = item['quantity']
        
        # تحديث عدد مرات شراء المنتج
        if product_name in product_purchase_count:
            product_purchase_count[product_name] += quantity
        else:
            product_purchase_count[product_name] = quantity
    
    # عرض المنتجات المتراكمة مع الكميات (مرقمة)
    message += "\n<b>تفاصيل المنتجات المتراكمة:</b>\n"
    counter = 1
    for product, quantity in product_purchase_count.items():
        message += f"{counter}. <b>{product}</b>: <font color='red'><b>{quantity}</b></font>\n"
        counter += 1
    
    # تحديث المجموع الإجمالي
    update_total_collected(total_amount)
    
    # إضافة 5 أسطر فارغة بين المجموع الإجمالي والبيانات السابقة
    message += "\n\n\n\n\n"  # 5 أسطر فارغة

    # عرض المجموع الإجمالي للمبالغ التي تم جمعها في آخر 24 ساعة
    message += "<b>المجموع الإجمالي خلال آخر 24 ساعة:</b>\n"
    message += f"المجموع: <font color='green'><b>{total_collected:.2f} {data['data']['total']['currency']}</b></font>\n"
    
    # إرسال الرسالة إلى تيليجرام
    send_to_telegram(message)
    
    return "تم الاستلام", 200

# تشغيل التطبيق
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
