import telebot
import json
import os
from telebot import types
import configparser

# Get the directory of the current script
base_dir = os.path.dirname(__file__)
bot_main_dir = os.path.join(base_dir, 'Bot Main')

# Membaca file konfigurasi
config_parser = configparser.ConfigParser()
config_file_path = os.path.join(base_dir, 'bot_config.txt')

if not os.path.exists(config_file_path):
    raise FileNotFoundError(f"Configuration file not found: {config_file_path}")

config_parser.read(config_file_path)

# Mengambil nilai dari file konfigurasi
try:
    token = config_parser['DEFAULT']['BOT_TOKEN']
    bot_owner_id = int(config_parser['DEFAULT']['BOT_OWNER_ID'])
    media_path = config_parser['DEFAULT']['MEDIA_PATH']  # Read MEDIA_PATH from bot_config.txt
    media_broadcast_path = config_parser['DEFAULT']['MEDIA_BROADCAST_PATH']
except KeyError as e:
    raise KeyError(f"Missing required configuration key: {e}")

bot = telebot.TeleBot(token)

# Use absolute path for config.json
config_file = os.path.join(base_dir, 'config.json')

# Default configuration
default_config = {
    'welcome_message': 'Welcome to ECWON88, how can I help you ?',
    'media_number': 1,
    'media_type': 'video',
    'join_my_url': 't.me/ecwonmyc',
    'join_sg_url': 't.me/ecwonsgc',
    'freecr_365_url': 'https://t.me/ec711bot',
    'join_my_text': 'JOIN MY🇲🇾',
    'join_sg_text': 'JOIN SG🇸🇬',
    'freecr_365_text': '🤑 FREE CREDIT 🤑',
    'admins': [bot_owner_id],
    'custom_buttons': [],
    'new_post_media_type': '',
    'new_post_caption': '',
    'media_path': media_path,
}

# Load configuration from file or create default if not exists
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
else:
    config = default_config
    with open(config_file, 'w') as f:
        json.dump(config, f)

# Extract bot_admin_ids from config
bot_admin_ids = config.get('admins', [])

# Save configuration to file
def save_config():
    with open(config_file, 'w') as f:
        json.dump(config, f)

# File to store user chat IDs and usernames
user_chat_ids_file = os.path.join(bot_main_dir, 'user_chat_ids.json')
excel_file = os.path.join(bot_main_dir, 'user_data.xlsx')

# Load user chat IDs and usernames from file
if os.path.exists(user_chat_ids_file):
    with open(user_chat_ids_file, 'r') as f:
        user_chat_ids = json.load(f)
        # Ensure user_chat_ids is a dictionary
        if not isinstance(user_chat_ids, dict):
            user_chat_ids = {}
else:
    user_chat_ids = {}

def back_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Back"))
    keyboard.add(types.KeyboardButton("Start Over"))
    return keyboard

def special_promotion_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Special Promotion"))
    return keyboard