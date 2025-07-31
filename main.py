import os
import re
import time
import config
import telebot
from telebot import types
from yt_dlp import YoutubeDL

# Bot Setup
bot = telebot.TeleBot(config.token)

# In-Memory User Database
user_db = {}  # Format: user_id: {'count': int, 'last_reset': date}

# Supported Platforms
SUPPORTED_SITES = ["youtube.com", "youtu.be", "instagram.com", "facebook.com", "twitter.com"]

# Messages
START_MSG = """👋 Welcome to Anything For You Bot!

Send any supported video link (YouTube, Instagram, Facebook, etc.)

💡 You get 4 downloads per day for free. 📺 Watch ads to unlock 6 more (max 10/day).

Type /help to see all commands."""

HELP_MSG = """🛠 Bot Commands:
/start - Welcome message
/help - List of commands
/info - Usage info
/reset - Reset daily download count
/language - Change bot language
/watch_ad - Watch ad to get 2 more downloads
"""

# Buttons
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 Download", "🎦 Watch Ad")
    markup.row("ℹ️ Info", "❓ Help")
    return markup

# Check if URL is supported
def is_supported(url):
    return any(site in url for site in SUPPORTED_SITES)

# Get user's data
def get_user_data(user_id):
    today = time.strftime("%Y-%m-%d")
    if user_id not in user_db:
        user_db[user_id] = {'count': 0, 'last_reset': today}
    elif user_db[user_id]['last_reset'] != today:
        user_db[user_id] = {'count': 0, 'last_reset': today}
    return user_db[user_id]

# Reset limit daily
def reset_daily_limit(user_id):
    user_db[user_id] = {'count': 0, 'last_reset': time.strftime("%Y-%m-%d")}

# Download Function
def download_video(url):
    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'format': 'best',
            'quiet': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"Download error: {e}")
        return None

# Start
@bot.message_handler(commands=['start'])
def start_msg(message):
    bot.send_message(message.chat.id, START_MSG, reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def help_msg(message):
    bot.send_message(message.chat.id, HELP_MSG)

@bot.message_handler(commands=['info'])
def show_info(message):
    user = get_user_data(message.from_user.id)
    bot.send_message(message.chat.id, f"📊 Downloads today: {user['count']}/10")

@bot.message_handler(commands=['reset'])
def reset_user(message):
    reset_daily_limit(message.from_user.id)
    bot.send_message(message.chat.id, "✅ Your daily limit has been reset.")

# Handle Ad Watch
@bot.message_handler(func=lambda m: m.text == "🎦 Watch Ad")
def watch_ad(message):
    user = get_user_data(message.from_user.id)
    if user['count'] >= 10:
        bot.send_message(message.chat.id, "🚫 Daily limit reached (10/10).")
        return
    user['count'] = min(user['count'] + 2, 10)
    bot.send_message(message.chat.id, "🎉 You earned 2 extra downloads! Keep going!")

# Handle URLs
@bot.message_handler(func=lambda m: re.search(r'https?://', m.text))
def handle_url(message):
    user = get_user_data(message.from_user.id)
    if user['count'] >= 10:
        bot.send_message(message.chat.id, "🚫 You've reached your 10 download limit today.")
        return

    url = message.text.strip()
    if not is_supported(url):
        bot.send_message(message.chat.id, "❌ Unsupported link. Try YouTube, Insta, FB, etc.")
        return

    msg = bot.send_message(message.chat.id, "⏬ Downloading, please wait...")
    file_path = download_video(url)

    if file_path:
        try:
            with open(file_path, 'rb') as f:
                bot.send_video(message.chat.id, f)
            user['count'] += 1
            os.remove(file_path)
        except Exception as e:
            print(f"Send error: {e}")
            bot.send_message(message.chat.id, "❌ Error sending video.")
    else:
        bot.send_message(message.chat.id, "❌ Failed to download video.")

# Fallback
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "❓ Send a valid link or use /help for guidance.")

print("🤖 Bot is running...")
bot.infinity_polling()
