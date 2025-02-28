import os
import random
import telebot
import time
import requests
import pandas as pd
import logging
import json
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
from googleapiclient.errors import HttpError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
script_dir = os.path.dirname(__file__)

GOOGLE_DRIVE_CREDENTIALS_FILE = os.path.join(script_dir, '..', 'utils', 'setup', 'CREDENTIALS_FILE.json')

token_file_path = os.path.join(script_dir, 'TOKEN & PATH2.txt')
buttons_file_path = os.path.join(script_dir, 'buttons2.json')

with open(token_file_path, 'r') as file:
    lines = file.readlines()
    BOT_TOKEN = lines[1].split('=', 1)[1].strip()
    BOT_OWNER_ID = lines[2].split('=', 1)[1].strip()
    GOOGLE_DRIVE_FOLDER_ID = lines[3].split('=', 1)[1].strip()
    CHANNELS = lines[4].split('=', 1)[1].strip().split(',')
    GROUPS = lines[5].split('=', 1)[1].strip().split(',')

with open(buttons_file_path, 'r', encoding='utf-8') as f:
    buttons_config = json.load(f)

bot = telebot.TeleBot(BOT_TOKEN)

def initialize_sheets_api():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_DRIVE_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    sheets_service = build('sheets', 'v4', credentials=creds)
    return sheets_service

def save_user_data_to_sheets(user_id, username, phone_number, interaction_time):
    sheets_service = initialize_sheets_api()
    spreadsheet_id = '1x9B-XxkJPsbkKguw6zAOFO8YPEDzqRooLJA_OefKsVU'
    range_name = 'AV 2 BOT!A1:D1'

    values = [
        [user_id, username, phone_number, interaction_time]
    ]
    body = {
        'values': values
    }
    try:
        result = sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption='RAW', body=body).execute()
        logging.info(f"{result.get('updates').get('updatedCells')} cells appended.")
    except HttpError as err:
        logging.error(f"An error occurred: {err}")
        
def initialize_drive_api():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_DRIVE_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    drive_service = build('drive', 'v3', credentials=creds)
    return drive_service

def get_video_files_from_drive(drive_service):
    query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and mimeType contains 'video/'"
    try:
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        logging.info(f"Found {len(files)} video files in the folder.")
        return files
    except HttpError as err:
        logging.error(f"An error occurred: {err}")
        return []

def download_video_from_drive(drive_service, file_id, user_id, username, chat_id, wait_message_id):
    request = drive_service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request, chunksize=5*1024*1024)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        progress = int(status.progress() * 100)
        logging.info(f"User {username} (ID: {user_id}): Download {progress}%.")
        bot.edit_message_text(chat_id=chat_id, message_id=wait_message_id, text=f"Download {progress}%")
    fh.seek(0)
    bot.edit_message_text(chat_id=chat_id, message_id=wait_message_id, text="Receive Video: 100%")
    return fh

drive_service = initialize_drive_api()

caption_file_path = os.path.join(script_dir, 'CAPTION2.txt')

with open(caption_file_path, 'r', encoding='utf-8') as file:
    CAPTION = file.read().strip()

def save_user_data(user_id, username, phone_number):
    file_path = os.path.join(script_dir, 'user_data.xlsx')
    data = {
        'User ID': [user_id],
        'Username': [username],
        'Phone Number': [phone_number],
        'First Interaction': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    }
    df = pd.DataFrame(data)
    
    if os.path.exists(file_path):
        existing_df = pd.read_excel(file_path)
        df = pd.concat([existing_df, df], ignore_index=True)
    
    df.to_excel(file_path, index=False)

@bot.message_handler(commands=['start'])
def check_subscription(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if str(user_id) == BOT_OWNER_ID:
        logging.info(f"Owner {username} (ID: {user_id}) pressed start.")
        wait_message = bot.send_message(message.chat.id, "Please wait a moment, your video is being sent")
        send_random_video(message, wait_message.message_id)
        return

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_phone = telebot.types.KeyboardButton(text="Share Now", request_contact=True)
    markup.add(button_phone)
    bot.send_message(message.chat.id, "To ensure a secure experience and prevent fake accounts or bots, kindly share your contact information before using this bot. We appreciate your understanding and cooperation!.", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    username = message.from_user.username
    phone_number = message.contact.phone_number
    interaction_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    save_user_data_to_sheets(user_id, username, phone_number, interaction_time)

    # Remove the keyboard
    markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Thanks for verifying that you're not a robot or fake account! 😊", reply_markup=markup)

    incomplete_channels = get_incomplete_channels(user_id)
    
    if incomplete_channels:
        markup = create_subscription_markup(incomplete_channels)
        bot.reply_to(message, "Please join our channel and group first to play the video.", reply_markup=markup)
    else:
        wait_message = bot.send_message(message.chat.id, "Please wait a moment, your video is being sent")
        send_random_video(message, wait_message.message_id)

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

def load_buttons_config():
    buttons_file_path = os.path.join(script_dir, 'buttons2.json')
    try:
        with open(buttons_file_path, 'r', encoding='utf-8') as file:
            buttons_config = json.load(file)
        return buttons_config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading buttons configuration: {e}")
        return {}

def send_random_video(message, wait_message_id):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        logging.info(f"User {username} (ID: {user_id}) requested a video.")

        video_files = get_video_files_from_drive(drive_service)
        
        if not video_files:
            bot.reply_to(message, "No videos found.")
            return
        
        random_video = random.choice(video_files)
        video_id = random_video['id']
        video_name = random_video['name']
        
        logging.info(f"User {username} (ID: {user_id}): Selected video: {video_name}")
    
        video_file = download_video_from_drive(drive_service, video_id, user_id, username, message.chat.id, wait_message_id)
        
        buttons_config = load_buttons_config()
        markup = InlineKeyboardMarkup()
        
        # Add existing buttons
        if buttons_config:
            if buttons_config.get('get_more_fun', {}).get('visible', False):
                markup.add(InlineKeyboardButton(buttons_config['get_more_fun']['name'], url=buttons_config['get_more_fun']['url']))
            if buttons_config.get('claim_bonus_my', {}).get('visible', False):
                markup.add(InlineKeyboardButton(buttons_config['claim_bonus_my']['name'], url=buttons_config['claim_bonus_my']['url']))
            if buttons_config.get('claim_bonus_sg', {}).get('visible', False):
                markup.add(InlineKeyboardButton(buttons_config['claim_bonus_sg']['name'], url=buttons_config['claim_bonus_sg']['url']))
        
        markup.row_width = 2
        markup.add(
            InlineKeyboardButton("▶️ Play & Next Video⏭️", callback_data="next_video")
        )
        
        if str(user_id) == BOT_OWNER_ID:
            markup.add(InlineKeyboardButton("⚙️Setting⚙️", callback_data="settings"))
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(KeyboardButton("🔄Start Over🔄"))
            

        start_time = time.time()
        send_video_with_retry(message.chat.id, video_file, CAPTION, markup, user_id, username, wait_message_id)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        logging.info(f"User {username} (ID: {user_id}): Sent video: {video_name} in {minutes}:{seconds:02d} (minutes:seconds)")
        
    except Exception as e:
        logging.error(f"User {username} (ID: {user_id}): Error sending video: {e}")
        bot.send_message(message.chat.id, "An error occurred while sending the video. Please try again.")

def send_video_with_retry(chat_id, video_file, caption, markup, user_id, username, wait_message_id, retries=3):
    for attempt in range(retries):
        try:
            video_file.seek(0, 2)
            file_size = video_file.tell()
            file_size_mb = file_size / (1024 * 1024)
            video_file.seek(0)

            logging.info(f"User {username} (ID: {user_id}): Sending video with size {file_size_mb:.2f} MB")

            bot.send_video(
                chat_id, 
                video_file, 
                caption=caption, 
                reply_markup=markup, 
                timeout=300  
            )
            bot.delete_message(chat_id, wait_message_id)
            return
        except Exception as e:
            logging.error(f"User {username} (ID: {user_id}): Error sending video on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(5)  
            
@bot.message_handler(func=lambda message: message.text == "🔄Start Over🔄")
def handle_start_over(message):
    check_subscription(message)

@bot.callback_query_handler(func=lambda call: call.data == "next_video")
def callback_next_video(call):
    user_id = call.from_user.id
    username = call.from_user.username
    logging.info(f"User {username} (ID: {user_id}) requested the next video.")
    wait_message = bot.send_message(call.message.chat.id, "Please wait a moment, your video is being sent")
    send_random_video(call.message, wait_message.message_id)

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
    wait_message = bot.send_message(call.message.chat.id, "Please wait a moment, your video is being sent")
    send_random_video(call.message, wait_message.message_id)

#MENU SETTINGS
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