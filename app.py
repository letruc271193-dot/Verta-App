import time
import telebot
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading

# --- CẤU HÌNH BOT & WEB ---
API_TOKEN = '8762431978:AAFQbSkjgzhI-GHR-TkHJtOvl-j4BD7CeOs'
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DRIVERS_TELEGRAM = {
    "36674469A": {"name": "Lê Anh Hào", "chat_id": 8507091430},
    "36674469B": {"name": "Lê Trung Trực", "chat_id": 8569322101},
    "36674469N": {"name": "Nguyễn Duy Vũ", "chat_id": 6796184126}
}

# --- GIAO DIỆN WEB ---
@app.route('/')
def index():
    return render_template('index.html')

# --- LẮNG NGHE TỪ WEB ---
@socketio.on('request_driver')
def handle_web_request(data):
    driver_code = data.get('driver_code')
    ride_type = data.get('ride_type')
    pickup = data.get('pickup')
    price = data.get('price')
    
    driver = DRIVERS_TELEGRAM.get(driver_code)
    if not driver:
        return

    try:
        raw_price = int(str(price).replace(',', '').replace('đ', '').strip())
        display_price = int(raw_price * 0.7)
        formatted_price = "{:,}đ".format(display_price)
    except:
        formatted_price = price

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btn1 = telebot.types.InlineKeyboardButton("✅ Nhận chuyến", callback_data=f"accept_{driver_code}")
    btn2 = telebot.types.InlineKeyboardButton("❌ Từ chối", callback_data=f"decline_{driver_code}")
    markup.add(btn1, btn2)

    msg = (f"🚨 **CÓ CHUYẾN MỚI!**\n\n"
           f"🚕 Loại xe: {ride_type}\n"
           f"📍 Điểm đón: {pickup}\n"
           f"💰 Giá nhận: {formatted_price}\n\n")

    bot.send_message(driver['chat_id'], msg, reply_markup=markup, parse_mode='Markdown')

# --- LẮNG NGHE TỪ TELEGRAM ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    bot.answer_callback_query(call.id)
    data = call.data.split('_')
    action = data[0]
    driver_code = data[1]

    if action == "accept":
        socketio.emit('driver_response', {'action': 'accept', 'driver_code': driver_code})
        bot.edit_message_text(f"✅ CHUYẾN ĐÃ NHẬN\n(Tài xế: {driver_code})",
                              call.message.chat_id, call.message.message_id)
    elif action == "decline":
        socketio.emit('driver_response', {'action': 'decline', 'driver_code': driver_code})
        bot.edit_message_text("❌ Đã từ chối chuyến.",
                              call.message.chat_id, call.message.message_id)

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling()

if __name__ == '__main__':
    # Chạy Bot Telegram chạy ngầm
    threading.Thread(target=run_bot, daemon=True).start()
    # Chạy Web Server ở cổng 5000
    socketio.run(app, host='0.0.0.0', port=5000)