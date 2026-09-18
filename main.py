from config import API_TOKEN
import sqlite3
import telebot
import threading
from flask import Flask

app = Flask('')


@app.route('/')
def home():
  return 'Bot is alive!'


def run():
  app.run(host='0.0.0.0', port=8080)


def keep_alive():
  t = threading.Thread(target=run)
  t.start()

bot = telebot.TeleBot(token = API_TOKEN)

conn = sqlite3.connect("bot_database.db", check_same_thread= False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
name TEXT,
balance REAL DEFAULT 0.0
)
"""
)
conn.commit()

def add_user(user_id, name):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)", (user_id, name)
    )
    conn.commit()

def get_user(user_id):
    cursor.execute(
        "SELECT name, balance FROM users WHERE user_id = ?", (user_id,)
    )
    return cursor.fetchone()

def update_balance(user_id, new_balance):
    cursor.execute(
        "UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id)
    )
    conn.commit()

def add_debt(user_id, amount):
    user_data = get_user(user_id)
    if user_data:
        current_balance = user_data[1]
        updated_balance = current_balance + amount
        update_balance(user_id, updated_balance)
        return updated_balance
    return None
def get_balance(user_id):
    user_info = get_user(user_id)
    if user_info:
        balance = user_info[1]
        return balance
    return None

def zero_balance(user_id):
    user_info = get_user(user_id)
    if user_info:
        reset = update_balance(user_id, 0.0)
        return True
    return False
    

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    fname = message.from_user.first_name
    add_user(uid, fname)
    user_info = get_user(uid)

    user_name = user_info[0]
    user_balance = user_info[1]
    text_response = (
        f"أهلا بك يا {user_name}\n رصيدك/دينك هو {user_balance}"
    )
    bot.reply_to(message, text_response)

@bot.message_handler(commands=['add_debt'])
def add_debt_cmd(message):
    uid = message.from_user.id

    msg_text = message.text.split()

    if len(msg_text) < 2:
        bot.reply_to(message, "لازم تكتب بهي الطريقة\n/add_debt 50")
        return 
    try:
        amount = float(msg_text[1])
        new_total = add_debt(uid, amount)
        if new_total is not None:
            bot.reply_to(message, f"تم اضافة المبلغ {amount}\nأصبح المبلغ الكامل {new_total}")
        else:
            bot.reply_to(message, "يجب عليك التسجيل أولا من /start")
    except ValueError:
        bot.reply_to(message, "يجب كتابة المبلغ بطريقة صحيحة")

@bot.message_handler(commands=['balance'])
def user_balance(message):
    uid = message.from_user.id
    b = get_balance(uid)
    if b is not None:
        bot.reply_to(message, f"دينك الحالي هو {b}")
    else:
        bot.reply_to(message, "يجب عليك البدء بتسجيل الدخول عن طريق /start")


@bot.message_handler(commands=['zero'])
def zero_cmd(message):
    uid = message.from_user.id
    success = zero_balance(uid)

    if success:
        bot.reply_to(message, f"لقد تم تصفير حسابك")
    else:
        bot.reply_to(message, "يجب عليك تسجيل الدخول من /start")
        
keep_alive()
    
bot.polling()

