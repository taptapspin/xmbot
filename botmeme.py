import os
import random
import telebot
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import yt_dlp as youtube_dl
import logging
import json
from configparser import ConfigParser

# Fungsi untuk memeriksa dan menghapus file log jika sudah lebih dari 10 hari
def check_and_clear_log_file(log_file, days=10):
    if os.path.exists(log_file):
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        if datetime.now() - file_mod_time > timedelta(days=days):
            os.remove(log_file)
            print(f"Log file {log_file} has been cleared.")

# Get the directory of the current script
script_dir = os.path.dirname(__file__)

# Nama file log
log_file = os.path.join(script_dir, 'bot_activity.log')

# Periksa dan hapus file log jika sudah lebih dari 10 hari
check_and_clear_log_file(log_file)

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=log_file, filemode='a')

# Tambahkan handler untuk menampilkan log di terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

buttons_file_path = os.path.join(script_dir, 'buttons3.json')

# Path to the TOKEN.txt file
token_file_path = os.path.join(script_dir, 'TOKEN.txt')

# Path to the CAPTION.txt file
caption_file_path = os.path.join(script_dir, 'CAPTION.txt')

# Path to your Google Drive API credentials JSON file
GOOGLE_DRIVE_CREDENTIALS_FILE = os.path.join(script_dir, '..', 'utils', 'setup', 'CREDENTIALS_FILE.json')

# Google Sheets ID
SPREADSHEET_ID = '1x9B-XxkJPsbkKguw6zAOFO8YPEDzqRooLJA_OefKsVU'  # Replace with your Google Sheets ID
RANGE_NAME = 'Meme Bot!A1:D1'  # Adjust the range as needed

# Read the configuration file with utf-8 encoding
config = ConfigParser()
with open(token_file_path, 'r', encoding='utf-8') as f:
    config.read_file(f)

# Read the caption file manually
with open(caption_file_path, 'r', encoding='utf-8') as f:
    CAPTION = f.read().strip()

# Load buttons configuration
with open(buttons_file_path, 'r', encoding='utf-8') as f:
    buttons_config = json.load(f)    

# Extract values from the configuration file
BOT_TOKEN = config.get('DEFAULT', 'TOKEN')
BOT_OWNER_ID = config.get('DEFAULT', 'BOT_OWNER_ID')
YT_API_KEY = config.get('DEFAULT', 'YOUTUBE API KEY')
CHANNELS = config.get('DEFAULT', 'CHANNEL USERNAME HERE').split(',')
GROUPS = config.get('DEFAULT', 'GROUP USERNAME HERE').split(',')
CHANNEL_SHARE = config.get('DEFAULT', 'CHANNEL SHARE')

bot = telebot.TeleBot(BOT_TOKEN)

# File to keep track of previously sent video URLs
video_history_file = os.path.join(script_dir, 'video_history.txt')

def load_video_history():
    if os.path.exists(video_history_file):
        with open(video_history_file, 'r') as file:
            return [line.strip() for line in file.readlines()]
    return []

def save_video_history(videos):
    with open(video_history_file, 'w') as file:
        file.write('\n'.join(videos))

def add_to_video_history(video_url):
    video_history = load_video_history()
    video_history.append(video_url)
    if len(video_history) > 1000:
        video_history = video_history[-1000:]  # Keep only the last 1000 entries
    save_video_history(video_history)

video_history = load_video_history()

def initialize_sheets_api():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_DRIVE_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    sheets_service = build('sheets', 'v4', credentials=creds)
    return sheets_service

def save_user_data_to_sheets(user_id, username, phone_number):
    sheets_service = initialize_sheets_api()
    interaction_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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

# Replace the existing save_user_data function with the new one
def save_user_data(user_id, username, phone_number):
    save_user_data_to_sheets(user_id, username, phone_number)

@bot.message_handler(commands=['start'])
def check_subscription(message):
    user_id = message.from_user.id
    username = message.from_user.username
    phone_number = message.contact.phone_number if message.contact else 'N/A'
    
    save_user_data(user_id, username, phone_number)
    
    incomplete_channels = get_incomplete_channels(user_id)
    
    if incomplete_channels:
        markup = create_subscription_markup(incomplete_channels)
        bot.reply_to(message, "Please join our channel and group first to play the video.", reply_markup=markup)
        logging.info(f"User {user_id} needs to join channels/groups: {incomplete_channels}")
    else:
        send_random_video(message, user_id)
        logging.info(f"User {user_id} is subscribed to all required channels/groups")

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

def get_youtube_shorts(api_key, query="shorts"):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.search().list(
            part="snippet",
            maxResults=10,  # Increase the number of results
            q=query,
            type="video",
            videoDuration="short"
        )
        response = request.execute()
        
        video_urls = []
        for item in response['items']:
            video_id = item['id']['videoId']
            video_urls.append(f"https://www.youtube.com/watch?v={video_id}")
        
        logging.info(f"Fetched YouTube shorts for query '{query}'")
        return video_urls
    except Exception as e:
        logging.error(f"Error fetching videos: {e}")
        return []

def download_youtube_video(url):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(script_dir, 'downloaded_video.mp4'),
            'quiet': True,
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        logging.info(f"Downloaded video from URL: {url}")
        return os.path.join(script_dir, 'downloaded_video.mp4')
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return None
    
def read_categories():
    categories_file_path = os.path.join(script_dir, 'CATEGORY.txt')
    with open(categories_file_path, 'r', encoding='utf-8') as file:
        categories = [line.strip() for line in file.readlines()]
    return categories

CATEGORIES = read_categories()

def send_random_video(message, user_id):
    try:
        query = random.choice(CATEGORIES)
        videos = get_youtube_shorts(YT_API_KEY, query)
        
        if not videos:
            bot.reply_to(message, "Tidak ada video yang ditemukan.")
            logging.info("No videos found for query")
            return
        
        random.shuffle(videos)  # Shuffle the list of videos to add randomness
        
        for video_url in videos:
            if video_url in video_history:
                logging.info(f"Skipping previously sent video: {video_url}")
                continue
            
            video_path = download_youtube_video(video_url)
            
            if video_path and os.path.getsize(video_path) > 0:
                markup = InlineKeyboardMarkup()
                
                # Add buttons from buttons3.json
                for button_key, button in buttons_config.items():
                    if button['visible']:
                        markup.add(InlineKeyboardButton(button['name'], url=button['url']))
                
                markup.row_width = 2
                markup.add(
                    InlineKeyboardButton("▶️ Play & Next Video⏭️", callback_data="next_video")
                )
                if str(user_id) == BOT_OWNER_ID:
                   markup.add(InlineKeyboardButton("⚙️ Settings ⚙️", callback_data="settings"))
                
                try:
                    with open(video_path, 'rb') as video:
                        sent_message = bot.send_video(
                            message.chat.id, 
                            video, 
                            caption=CAPTION, 
                            reply_markup=markup,
                            timeout=180  # Set timeout to 3 minutes
                        )
                        bot.forward_message(
                            CHANNEL_SHARE, 
                            sent_message.chat.id, 
                            sent_message.message_id
                        )
                    
                    os.remove(video_path)
                    add_to_video_history(video_url)
                    logging.info(f"Video sent to user")
                    return
                except Exception as e:
                    logging.error(f"Error sending video: {e}")
                    continue  # Try the next video if sending fails
            
            else:
                logging.info(f"Skipping video {video_url} due to download error or empty file.")
        
        # If all fetched videos are already sent, fetch new videos
        bot.reply_to(message, "Gagal mengunduh video yang valid. Mencoba lagi...")
        send_random_video(message, user_id)
    except Exception as e:
        bot.send_message(message.chat.id, "Please wait a moment, your video is being sent")
        logging.error(f"Error sending video: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "next_video")
def callback_next_video(call):
    bot.send_message(call.message.chat.id, "Please wait a moment, your video is being sent")
    logging.info(f"User {call.from_user.id} {call.from_user.username} requested next video")
    send_random_video(call.message, call.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data == "play")
def callback_play(call):
    incomplete_channels = get_incomplete_channels(call.from_user.id)
    
    if incomplete_channels:
        markup = create_subscription_markup(incomplete_channels)
        bot.send_message(call.message.chat.id, "Please join our channel and group first to play the video.", reply_markup=markup)
        logging.info(f"User {call.from_user.id} needs to join channels/groups: {incomplete_channels}")
    else:
        bot.send_message(call.message.chat.id, "Congratulations! You have completed all the requirements. Press ▶️ Play ▶️ to play the video.")
        bot.send_message(call.message.chat.id, "Press here ", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="▶️ Play ▶️", callback_data="play_final")]]))
        logging.info(f"User {call.from_user.id} is subscribed to all required channels/groups")

@bot.callback_query_handler(func=lambda call: call.data == "play_final")
def callback_play_final(call):
    logging.info(f"User {call.message.chat.id} pressed play final")
    send_random_video(call.message, call.from_user.id)

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
    markup.add(InlineKeyboardButton("🔄Home🔄", callback_data="next_video"))
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

if __name__ == "__main__":
    run_bot()