import threading
import time
import telebot
from flask import Flask, render_template
from flask_socketio import SocketIO

# --- CẤU HÌNH BOT TELEGRAM ---
API_TOKEN = '8762431978:AAFQbSkjgzhI-GHR-TkHJtOvl-j4BD7CeOs'
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

DRIVERS_TELEGRAM = {
    "36674469A": {"name": "Lê Anh Hào", "chat_id": 8507091430},
    "36674469B": {"name": "Lê Trung Trực", "chat_id": 8569322101},
    "36674469N": {"name": "Nguyễn Duy Vũ", "chat_id": 6796184126}
}

# --- ROUTE GIAO DIỆN ---
@app.route('/')
def index():
    return render_template('index.html')

# --- LẮNG NGHE YÊU CẦU ĐẶT XE TỪ WEB ---
@socketio.on('request_driver')
def handle_web_request(data):
    driver_code = data.get('driver_code')
    ride_type = data.get('ride_type')
    pickup = data.get('pickup')
    price = data.get('price')
    
    driver = DRIVERS_TELEGRAM.get(driver_code)
    if not driver:
        print(f"❌ Không tìm thấy tài xế: {driver_code}")
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

    try:
        bot.send_message(driver['chat_id'], msg, reply_markup=markup, parse_mode='Markdown')
    except Exception as e:
        print(f"❌ Lỗi gửi tin Telegram: {e}")

# --- LẮNG NGHE PHẢN HỒI TỪ TÀI XẾ (TELEGRAM) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    print(f"📡 ĐÃ NHẬN CALLBACK TỪ TELEGRAM: {call.data}")
    bot.answer_callback_query(call.id)

    data = call.data.split('_')
    action = data[0]
    driver_code = data[1]

    if action == "accept":
        print(f"✅ Đang xử lý lệnh nhận chuyến cho: {driver_code}")
        try:
            # Bắn tín hiệu về Web
            socketio.emit('driver_response', {'action': 'accept', 'driver_code': driver_code})
            bot.edit_message_text(f"✅ CHUYẾN ĐÃ NHẬN\n(Tài xế: {driver_code})",
                                  call.message.chat_id, call.message.message_id)
        except Exception as e:
            print(f"❌ Lỗi truyền tin: {e}")

    elif action == "decline":
        try:
            socketio.emit('driver_response', {'action': 'decline', 'driver_code': driver_code})
            bot.edit_message_text("❌ Đã từ chối chuyến.",
                                  call.message.chat_id, call.message.message_id)
        except Exception as e:
            print(f"❌ Lỗi truyền tin: {e}")

def run_polling():
    print("🤖 Verta Bot đang kết nối...")
    bot.remove_webhook()
    bot.infinity_polling(timeout=60, long_polling_timeout=30)

if __name__ == '__main__':
    # Khởi chạy bot trong thread riêng
    threading.Thread(target=run_polling, daemon=True, name="VertaThread").start()
    print("🚀 Verta Web & Bot Online & Ready!")
    # Khởi chạy Web Server
    socketio.run(app, host='0.0.0.0', port=5000)