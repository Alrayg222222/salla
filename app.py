from flask import Flask, request
import requests
import os
from datetime import datetime, timedelta
import pytz  # لإدارة المنطقة الزمنية

app = Flask(__name__)

# إعداد التوكنات و IDs
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SECOND_CHAT_ID = os.environ.get("SECOND_CHAT_ID")

# المنطقة الزمنية للرياض
riyadh_tz = pytz.timezone("Asia/Riyadh")

# المتغيرات التراكمية
total_collected = 0
weekly_collected = 0
monthly_collected = 0
product_purchase_count = {}

# إعداد توقيتات التصفير
now = datetime.now(riyadh_tz)
last_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

# بداية الأسبوع: آخر أربعاء سابق أو اليوم إذا كان هو الأربعاء
days_since_wednesday = (now.weekday() - 2) % 7
last_weekly_reset_time = (now - timedelta(days=days_since_wednesday)).replace(hour=0, minute=0, second=0, microsecond=0)

# بداية الشهر
last_monthly_reset_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

# دالة الإرسال إلى تيليجرام
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in [CHAT_ID, SECOND_CHAT_ID]:
        if chat_id:
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            try:
                requests.post(url, data=payload)
            except Exception as e:
                print(f"خطأ أثناء الإرسال إلى Telegram: {e}")

# دالة تحديث المجاميع
def update_total_collected(amount):
    global total_collected, weekly_collected, monthly_collected
    global last_reset_time, last_weekly_reset_time, last_monthly_reset_time
    global product_purchase_count

    current_time = datetime.now(riyadh_tz)

    # تصفير اليومي
    if current_time >= last_reset_time + timedelta(days=1):
        total_collected = 0
        last_reset_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        product_purchase_count.clear()

    # تصفير الأسبوعي (كل أربعاء 12 صباحًا)
    if current_time >= last_weekly_reset_time + timedelta(days=7):
        weekly_collected = 0
        last_weekly_reset_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    # تصفير الشهري (كل 1 ميلادي 12 صباحًا)
    if current_time.month != last_monthly_reset_time.month or current_time.year != last_monthly_reset_time.year:
        monthly_collected = 0
        last_monthly_reset_time = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # تحديث المجاميع
    total_collected += amount
    weekly_collected += amount
    monthly_collected += amount

# Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    # استخراج البيانات
    order_data = data.get("data", {})
    total_amount = order_data.get("total", {}).get("amount", 0)
    currency = order_data.get("total", {}).get("currency", "SAR")
    items = order_data.get("items", [])

    # بداية الرسالة
    message = "<b>💸شراء💸</b> <b>{:.2f} {}</b> ".format(total_amount, currency)

    for item in items:
        name = item.get("name", "")
        short_name = " ".join(name.split()[:2])
        message += f"({short_name}) "

    message += "\n\n\n" + "🎉" * 13 + "\n"

    # تفاصيل المنتجات (أول 4 كلمات فقط)
    message += "\n<b>تفاصيل المنتجات:</b>\n"
    for item in items:
        full_name = item.get("name", "")
        short_name = " ".join(full_name.split()[:4])
        quantity = item.get("quantity", 1)
        price = item.get("total", {}).get("amount", 0)
        message += f"- <b>{short_name}</b> x{quantity}\n"
        message += f"  السعر: <b>{price:.2f} {currency}</b>\n"

    # تحديث عداد المنتجات
    for item in items:
        name = item.get("name", "")
        quantity = item.get("quantity", 1)
        product_purchase_count[name] = product_purchase_count.get(name, 0) + quantity

    # عرض المنتجات المشتراة اليوم
    message += "\n" + "🎉" * 13 + "\n"
    message += "<b>المنتجات التي تم شراءها اليوم:</b>\n"
    for product, quantity in product_purchase_count.items():
        short_name = " ".join(product.split()[:3])
        message += f"• ⚽{quantity}⚽ <b>{short_name}</b>\n"
    message += "🎉" * 13 + "\n"

    # تحديث التراكمي
    update_total_collected(total_amount)

    # المجموعات
    message += "\n\n💰 <b>دخلنا اليوم:</b>\n"
    message += f"💵 <b>{total_collected:.2f} {currency}</b>\n"

    message += "\n💼 <b>دخلنا هذا الأسبوع:</b>\n"
    message += f"📈 <b>{weekly_collected:.2f} {currency}</b>\n"

    message += "\n📅 <b>دخلنا هذا الشهر:</b>\n"
    message += f"🪙 <b>{monthly_collected:.2f} {currency}</b>\n"

    # إرسال الرسالة
    send_to_telegram(message)

    return "تم الاستلام", 200

# تشغيل التطبيق
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
