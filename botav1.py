import os
import random
import telebot
import time
import requests
import logging
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from configparser import ConfigParser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_bot():
    while True:
        try:
            logging.info("Starting bot polling...")
            bot.polling(timeout=180, long_polling_timeout=180)
            logging.info("Bot polling started.")
        except Exception as e:
            logging.error(f"Bot terminated with error: {e}")
            logging.info("Restarting bot in 5 seconds...")
            time.sleep(5)

# Get the directory of the current script
script_dir = os.path.dirname(__file__)

# Path to the TOKEN & PATH1.txt file
config_file_path = os.path.join(script_dir, 'TOKEN & PATH1.txt')

# Path to the CAPTION1.txt file
caption_file_path = os.path.join(script_dir, 'CAPTION1.txt')

# Path to the buttons1.json file
buttons_file_path = os.path.join(script_dir, 'buttons1.json')

# Path to your Google Drive API credentials JSON file
GOOGLE_DRIVE_CREDENTIALS_FILE = os.path.join(script_dir, '..', 'utils', 'setup', 'CREDENTIALS_FILE.json')

# Google Sheets ID
SPREADSHEET_ID = '1x9B-XxkJPsbkKguw6zAOFO8YPEDzqRooLJA_OefKsVU'  # Replace with your Google Sheets ID
RANGE_NAME = 'AV 1 BOT!A1:D1'  # Adjust the range as needed

# Read the configuration file with utf-8 encoding
config = ConfigParser()
with open(config_file_path, 'r', encoding='utf-8') as f:
    config.read_file(f)

# Read the caption file manually
with open(caption_file_path, 'r', encoding='utf-8') as f:
    CAPTION = f.read().strip()

# Read the buttons configuration file
with open(buttons_file_path, 'r', encoding='utf-8') as f:
    buttons_config = json.load(f)

# Extract values from the configuration file
BOT_TOKEN = config.get('DEFAULT', 'bot_token')
VIDEO_FOLDER_PATH = config.get('DEFAULT', 'media_path')
CHANNELS = config.get('DEFAULT', 'channel_username').split(',')
GROUPS = config.get('DEFAULT', 'group_username').split(',')
BOT_OWNER_ID = config.getint('DEFAULT', 'bot_owner_id')

# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)

def initialize_sheets_api():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_DRIVE_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    sheets_service = build('sheets', 'v4', credentials=creds)
    return sheets_service

def save_user_data_to_sheets(user_id, username, phone_number):
    sheets_service = initialize_sheets_api()
    interaction_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    values = [
        [user_id, username, phone_number, interaction_time]
    ]
    body = {
        'values': values
    }
    try:
        result = sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
            valueInputOption='RAW', body=body).execute()
        logging.info(f"{result.get('updates').get('updatedCells')} cells appended.")
    except HttpError as err:
        logging.error(f"An error occurred: {err}")

@bot.message_handler(commands=['start'])
def check_subscription(message):
    user_id = message.from_user.id
    username = message.from_user.username
    phone_number = message.contact.phone_number if message.contact else 'N/A'
    
    save_user_data_to_sheets(user_id, username, phone_number)
    
    incomplete_channels = get_incomplete_channels(user_id)
    
    if incomplete_channels:
        markup = create_subscription_markup(incomplete_channels)
        bot.reply_to(message, "Please join our channel and group first to play the video.", reply_markup=markup)
    else:
        send_random_video(message)

def get_incomplete_channels(user_id):
    incomplete_channels = []
    for channel in CHANNELS:
        try:
            member_status = bot.get_chat_member(channel, user_id).status
            if member_status not in ['member', 'administrator', 'creator']:
                incomplete_channels.append({"name": "Channel", "username": channel})
        except Exception as e:
            logging.error(f"Error checking channel {channel}: {e}")
    for group in GROUPS:
        try:
            member_status = bot.get_chat_member(group, user_id).status
            if member_status not in ['member', 'administrator', 'creator']:
                incomplete_channels.append({"name": "Group", "username": group})
        except Exception as e:
            logging.error(f"Error checking group {group}: {e}")
    return incomplete_channels

def create_subscription_markup(channels):
    markup = InlineKeyboardMarkup()
    for channel in channels:
        markup.add(InlineKeyboardButton(f"Join {channel['name']}", url=f"https://t.me/{channel['username'][1:]}"))
    markup.add(InlineKeyboardButton("▶️ Play ▶️", callback_data="play"))
    return markup

def send_random_video(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        logging.info(f"User {username} (ID: {user_id}) requested a video.")

        video_files = [f for f in os.listdir(VIDEO_FOLDER_PATH) if os.path.isfile(os.path.join(VIDEO_FOLDER_PATH, f))]
        
        if not video_files:
            bot.reply_to(message, "Tidak ada video yang ditemukan.")
            return
        
        random.shuffle(video_files)
        
        for random_video in video_files:
            video_path = os.path.join(VIDEO_FOLDER_PATH, random_video)
            
            # Log video yang dipilih
            logging.info(f"Selected video: {random_video}")
            
            # Check file size
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            logging.info(f"Video size: {file_size_mb:.2f} MB")
            
            video_to_send = video_path
            
            markup = InlineKeyboardMarkup()
            if buttons_config["get_more_fun"]["visible"]:
                markup.add(InlineKeyboardButton(buttons_config["get_more_fun"]["name"], url=buttons_config["get_more_fun"]["url"]))
            markup.row_width = 2
            if buttons_config["claim_bonus_my"]["visible"]:
                markup.add(InlineKeyboardButton(buttons_config["claim_bonus_my"]["name"], url=buttons_config["claim_bonus_my"]["url"]))
            if buttons_config["claim_bonus_sg"]["visible"]:
                markup.add(InlineKeyboardButton(buttons_config["claim_bonus_sg"]["name"], url=buttons_config["claim_bonus_sg"]["url"]))
            markup.add(InlineKeyboardButton("▶️ Play & Next Video⏭️", callback_data="next_video"))
            
            # Add settings button for bot owner
            if user_id == BOT_OWNER_ID:
                markup.add(InlineKeyboardButton("⚙️ Settings ⚙️", callback_data="settings"))

            start_time = time.time()
            with open(video_to_send, 'rb') as video:
                for _ in range(1, 101):
                    try:
                        bot.send_video(
                            message.chat.id, 
                            video, 
                            caption=CAPTION, 
                            reply_markup=markup, 
                            timeout=180
                        )
                        break
                    except requests.exceptions.Timeout:
                        bot.send_message(message.chat.id, "Please wait a moment, your video is being sent")
                        time.sleep(1)
            end_time = time.time()
            
            elapsed_time = end_time - start_time
            minutes, seconds = divmod(int(elapsed_time), 60)
            logging.info(f"Sent video: {random_video} in {minutes}:{seconds:02d} (minutes:seconds)")
            
            break

        if user_id == BOT_OWNER_ID:
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(KeyboardButton("🔄Start Over🔄"))
            

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        bot.send_message(message.chat.id, "Please wait a moment, your video is being sent")

@bot.message_handler(func=lambda message: message.text == "🔄Start Over🔄")
def handle_start_over(message):
    check_subscription(message)
    
@bot.callback_query_handler(func=lambda call: call.data == "next_video")
def callback_next_video(call):
    user_id = call.from_user.id
    username = call.from_user.username
    logging.info(f"User {username} (ID: {user_id}) requested the next video.")
    bot.send_message(call.message.chat.id, "Please wait a moment, your video is being sent")
    send_random_video(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "play")
def callback_play(call):
    user_id = call.from_user.id
    username = call.from_user.username
    logging.info(f"User {username} (ID: {user_id}) pressed play.")
    
    incomplete_channels = get_incomplete_channels(user_id)
    
    if incomplete_channels:
        markup = create_subscription_markup(incomplete_channels)
        bot.send_message(call.message.chat.id, "Please join our channel and group first to play the video.", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "Congratulations! You have completed all the requirements. Press ▶️ Play ▶️ to play the video.")
        bot.send_message(call.message.chat.id, "Press here ", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="▶️ Play ▶️", callback_data="play_final")]]))

@bot.callback_query_handler(func=lambda call: call.data == "play_final")
def callback_play_final(call):
    user_id = call.from_user.id
    username = call.from_user.username
    logging.info(f"User {username} (ID: {user_id}) pressed play final.")
    send_random_video(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "settings")
def callback_settings(call):
    user_id = call.from_user.id
    username = call.from_user.username
    logging.info(f"User {username} (ID: {user_id}) accessed settings.")
    bot.send_message(call.message.chat.id, "Settings menu:", reply_markup=create_settings_markup())

def create_settings_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Edit Button Name", callback_data="edit_button_name"))
    markup.add(InlineKeyboardButton("Edit Button Link", callback_data="edit_button_link"))
    markup.add(InlineKeyboardButton("Show/Hide Button", callback_data="show_hide_button"))
    markup.add(InlineKeyboardButton("Back", callback_data="back"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "edit_button_name")
def callback_edit_button_name(call):
    markup = InlineKeyboardMarkup()
    for button_key, button_info in buttons_config.items():
        markup.add(InlineKeyboardButton(button_info["name"], callback_data=f"edit_name_{button_key}"))
    markup.add(InlineKeyboardButton("Back", callback_data="back"))
    bot.send_message(call.message.chat.id, "Select a button to edit its name:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_name_"))
def callback_select_button_to_edit(call):
    button_key = call.data[len("edit_name_"):]
    msg = bot.send_message(call.message.chat.id, f"Enter new name for the button '{buttons_config[button_key]['name']}':")
    bot.register_next_step_handler(msg, process_new_button_name, button_key)

def process_new_button_name(message, button_key):
    new_name = message.text
    buttons_config[button_key]['name'] = new_name
    with open(buttons_file_path, 'w', encoding='utf-8') as f:
        json.dump(buttons_config, f, ensure_ascii=False, indent=4)
    bot.send_message(message.chat.id, f"Button name updated to '{new_name}'.")
    bot.send_message(message.chat.id, "Returning to settings menu", reply_markup=create_settings_markup())


@bot.callback_query_handler(func=lambda call: call.data == "edit_button_link")
def callback_edit_button_link(call):
    markup = InlineKeyboardMarkup()
    for button_key, button_info in buttons_config.items():
        markup.add(InlineKeyboardButton(button_info["name"], callback_data=f"edit_link_{button_key}"))
    markup.add(InlineKeyboardButton("Back", callback_data="back"))
    bot.send_message(call.message.chat.id, "Select a button to edit its link:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_link_"))
def callback_select_button_to_edit_link(call):
    button_key = call.data[len("edit_link_"):]
    msg = bot.send_message(call.message.chat.id, f"Enter new link for the button '{buttons_config[button_key]['name']}':")
    bot.register_next_step_handler(msg, process_new_button_link, button_key)

def process_new_button_link(message, button_key):
    new_link = message.text
    buttons_config[button_key]['url'] = new_link
    with open(buttons_file_path, 'w', encoding='utf-8') as f:
        json.dump(buttons_config, f, ensure_ascii=False, indent=4)
    bot.send_message(message.chat.id, f"Button link updated to '{new_link}'.")
    bot.send_message(message.chat.id, "Returning to settings menu", reply_markup=create_settings_markup())

@bot.callback_query_handler(func=lambda call: call.data == "show_hide_button")
def callback_show_hide_button(call):
    markup = InlineKeyboardMarkup()
    for button_key, button_info in buttons_config.items():
        visibility = "Show" if not button_info["visible"] else "Hide"
        markup.add(InlineKeyboardButton(f"{button_info['name']} ({visibility})", callback_data=f"toggle_visibility_{button_key}"))
    markup.add(InlineKeyboardButton("Back", callback_data="back"))
    bot.send_message(call.message.chat.id, "Select a button to toggle its visibility:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_visibility_"))
def callback_toggle_visibility(call):
    button_key = call.data[len("toggle_visibility_"):]
    buttons_config[button_key]["visible"] = not buttons_config[button_key]["visible"]
    with open(buttons_file_path, 'w', encoding='utf-8') as f:
        json.dump(buttons_config, f, ensure_ascii=False, indent=4)
    visibility_status = "visible" if buttons_config[button_key]["visible"] else "hidden"
    bot.send_message(call.message.chat.id, f"Button '{buttons_config[button_key]['name']}' is now {visibility_status}.")
    bot.send_message(call.message.chat.id, "Returning to settings menu", reply_markup=create_settings_markup())

@bot.callback_query_handler(func=lambda call: call.data == "back")
def callback_back(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

def create_main_menu_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("▶️ Play ▶️", callback_data="play"))
    return markup

if __name__ == "__main__":
    run_bot()