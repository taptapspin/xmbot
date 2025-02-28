import json
import os
import openpyxl
from datetime import datetime
from telebot import types
from config import bot
import re
import logging
import glob
import sqlite3
import atexit
from config import back_keyboard, media_broadcast_path
import datetime

logging.basicConfig(level=logging.INFO)

def write_config(config):
    with open(config_file_path, 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, indent=4)

base_dir = os.path.dirname(__file__)

def get_db_connection():
    db_path = os.path.join(base_dir, 'broadcasts.db')
    conn = sqlite3.connect(db_path)
    return conn, conn.cursor()

conn, c = get_db_connection()
c.execute('DROP TABLE IF EXISTS posts')
c.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        media_path TEXT,
        caption TEXT,
        buttons TEXT,
        media_type TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()

successful_broadcast_count = 0  
failed_broadcast_count = 0

def send_broadcast_report(chat_id):
    global successful_broadcast_count, failed_broadcast_count  
    now = datetime.datetime.now()
    report_message = (
        f"Berhasil dikirim: {successful_broadcast_count}\n"
        f"Date & Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Failed: {failed_broadcast_count}\n\n"
        "note: Broadcast delivery failed because the bot was blocked by the user."
    )
    bot.send_message(chat_id, report_message)
    successful_broadcast_count = 0  
    failed_broadcast_count = 0  

@atexit.register
def close_db_connection():
    conn, c = get_db_connection()
    conn.close()

config_file_path = os.path.join(os.path.dirname(__file__), 'config.json')

if not os.path.exists(config_file_path):
    raise FileNotFoundError(f"Configuration file not found: {config_file_path}")

with open(config_file_path, 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

broadcast_options = [
    "Send Media", "Edit Media",
    "Add Caption", "Edit Caption",
    "Add Link Button", "Edit Link Button",
    "Delete Link Button",
    "Preview Message",
    "Send Broadcast",
    "Cancel"
]


current_media_number = 0
current_caption = ""
current_buttons = []
current_media_type = None  
latest_post_id = None  

def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  
        r'localhost|'  
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  
        r'(?::\d+)?' 
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def send_broadcast_menu(chat_id):
    broadcast_menu_keyboard = types.InlineKeyboardMarkup()
    
    # Add buttons as specified
    broadcast_menu_keyboard.add(
        types.InlineKeyboardButton(text="Add Media", callback_data="broadcast_send_media")
    )
    broadcast_menu_keyboard.row(
        types.InlineKeyboardButton(text="Edit Media", callback_data="broadcast_edit_media"),
        types.InlineKeyboardButton(text="Add Caption", callback_data="broadcast_add_caption"),
        types.InlineKeyboardButton(text="Edit Caption", callback_data="broadcast_edit_caption")
    )
    broadcast_menu_keyboard.row(
        types.InlineKeyboardButton(text="Add Link Button", callback_data="broadcast_add_link_button"),
        types.InlineKeyboardButton(text="Edit Link Button", callback_data="broadcast_edit_link_button"),
        types.InlineKeyboardButton(text="Delete Link Button", callback_data="broadcast_delete_link_button")
    )
    broadcast_menu_keyboard.add(
        types.InlineKeyboardButton(text="Preview Message", callback_data="broadcast_preview_message")
    )
    broadcast_menu_keyboard.add(
        types.InlineKeyboardButton(text="Send Broadcast", callback_data="broadcast_send_broadcast")
    )
    broadcast_menu_keyboard.add(
        types.InlineKeyboardButton(text="Cancel", callback_data="cancel8")
    )
    
    bot.send_message(chat_id, "Broadcast Menu:", reply_markup=broadcast_menu_keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("broadcast_") or call.data == "edit_post")
def handle_broadcast_menu(call):
    if call.data == "edit_post":
        send_broadcast_menu(call.message.chat.id)
    else:
        option = call.data.split("_", 1)[1]
        if option == "send_media":
            bot.send_message(call.message.chat.id, "Please send the media file.",reply_markup=back_keyboard())
            bot.register_next_step_handler(call.message, handle_send_media)
        elif option == "edit_media":
            bot.send_message(call.message.chat.id, "Please send the new media file.",reply_markup=back_keyboard())
            bot.register_next_step_handler(call.message, handle_edit_media)
        elif option == "add_caption":
            bot.send_message(call.message.chat.id, "Please send the caption.",reply_markup=back_keyboard())
            bot.register_next_step_handler(call.message, handle_caption)
        elif option == "edit_caption":
            bot.send_message(call.message.chat.id, "Please send the new caption.",reply_markup=back_keyboard())
            bot.register_next_step_handler(call.message, handle_caption)
        elif option == "add_link_button":
            bot.send_message(call.message.chat.id, "Please send the button text and URL in the format: text - url",reply_markup=back_keyboard())
            bot.register_next_step_handler(call.message, handle_add_link_button)
        elif option == "edit_link_button":
            bot.send_message(call.message.chat.id, "Please send the button text and new URL in the format: text,url",reply_markup=back_keyboard())
            bot.register_next_step_handler(call.message, handle_edit_link_button)
        elif option == "delete_link_button":
            bot.send_message(call.message.chat.id, "Please send the button text to delete.",reply_markup=back_keyboard())
            bot.register_next_step_handler(call.message, handle_delete_link_button)
        elif option == "preview_message":
            preview_message(call.message.chat.id)
        elif option == "send_broadcast":
            send_broadcast(call.message.chat.id)

def save_post_to_db(media_path, caption, buttons, media_type):
    conn, c = get_db_connection()
    c.execute("INSERT INTO posts (media_path, caption, buttons, media_type) VALUES (?, ?, ?, ?)",
              (media_path, caption, json.dumps(buttons), media_type))
    post_id = c.lastrowid
    conn.commit()
    conn.close()
    return post_id

def update_post_in_db(post_id, media_path, caption, buttons, media_type):
    conn, c = get_db_connection()
    c.execute("UPDATE posts SET media_path=?, caption=?, buttons=?, media_type=? WHERE id=?",
              (media_path, caption, json.dumps(buttons), media_type, post_id))
    conn.commit()
    conn.close()

def load_post_from_db(post_id):
    conn, c = get_db_connection()
    c.execute("SELECT media_path, caption, buttons, media_type FROM posts WHERE id=?", (post_id,))
    post = c.fetchone()
    conn.close()
    if post:
        media_path, caption, buttons, media_type = post
        buttons = json.loads(buttons)
        return media_path, caption, buttons, media_type
    return None

def load_user_chat_ids():
    try:
        file_path = os.path.join(base_dir, 'user_chat_ids.json')
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def handle_media(message):
    global current_media_number, current_media_type, latest_post_id
    if message.content_type in ['photo', 'video', 'document']:
        current_media_number += 1
        media_file_id = None
        current_media_type = message.content_type 
        if message.content_type == 'photo':
            media_file_id = message.photo[-1].file_id
        elif message.content_type == 'video':
            media_file_id = message.video.file_id
        elif message.content_type == 'document':
            media_file_id = message.document.file_id

        if media_file_id:
            file_info = bot.get_file(media_file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_extension = os.path.splitext(file_info.file_path)[1] 
            media_file_path = os.path.join(media_broadcast_path, f'media_{current_media_number}{file_extension}')
            with open(media_file_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            media_file_path = media_file_path.replace("\\", "/")
            logging.info(f"Downloaded media file path: {media_file_path}")

            file_size = os.path.getsize(media_file_path)
            logging.info(f"Downloaded media file size: {file_size} bytes")
            if file_size > 0:
                bot.send_message(message.chat.id, "Media saved successfully.",reply_markup=back_keyboard())
                if latest_post_id is None:
                    latest_post_id = save_post_to_db(media_file_path, current_caption, current_buttons, current_media_type)
                else:
                    update_post_in_db(latest_post_id, media_file_path, current_caption, current_buttons, current_media_type)
                preview_message(message.chat.id)  
            else:
                bot.send_message(message.chat.id, "Failed to save media. The file is empty.",reply_markup=back_keyboard())
                os.remove(media_file_path) 
    else:
        bot.send_message(message.chat.id, "Invalid media type. Please send a photo, video, or document.",reply_markup=back_keyboard())

def handle_send_media(message):
    global current_media_number, current_media_type, latest_post_id
    if message.content_type in ['photo', 'video', 'document']:
        current_media_number += 1
        media_file_id = None
        current_media_type = message.content_type  
        if message.content_type == 'photo':
            media_file_id = message.photo[-1].file_id
        elif message.content_type == 'video':
            media_file_id = message.video.file_id
        elif message.content_type == 'document':
            media_file_id = message.document.file_id

        if media_file_id:
            file_info = bot.get_file(media_file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_extension = os.path.splitext(file_info.file_path)[1]  
            media_file_path = os.path.join(media_broadcast_path, f'media_{current_media_number}{file_extension}')
            with open(media_file_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            media_file_path = media_file_path.replace("\\", "/")
            logging.info(f"Downloaded media file path: {media_file_path}")

            file_size = os.path.getsize(media_file_path)
            logging.info(f"Downloaded media file size: {file_size} bytes")
            if file_size > 0:
                bot.send_message(message.chat.id, "Media saved successfully.",reply_markup=back_keyboard())
                if latest_post_id is None:
                    latest_post_id = save_post_to_db(media_file_path, current_caption, current_buttons, current_media_type)
                else:
                    update_post_in_db(latest_post_id, media_file_path, current_caption, current_buttons, current_media_type)
                preview_message(message.chat.id) 
            else:
                bot.send_message(message.chat.id, "Failed to save media. The file is empty.",reply_markup=back_keyboard())
                os.remove(media_file_path)  
    else:
        bot.send_message(message.chat.id, "Invalid media type. Please send a photo, video, or document.",reply_markup=back_keyboard())

def handle_edit_media(message):
    global current_media_number, current_media_type, latest_post_id
    if message.content_type in ['photo', 'video', 'document']:
        current_media_number += 1
        media_file_id = None
        current_media_type = message.content_type 
        if message.content_type == 'photo':
            media_file_id = message.photo[-1].file_id
        elif message.content_type == 'video':
            media_file_id = message.video.file_id
        elif message.content_type == 'document':
            media_file_id = message.document.file_id

        if media_file_id:
            file_info = bot.get_file(media_file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_extension = os.path.splitext(file_info.file_path)[1] 
            media_file_path = os.path.join(media_broadcast_path, f'media_{current_media_number}{file_extension}')
            with open(media_file_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            media_file_path = media_file_path.replace("\\", "/")
            logging.info(f"Downloaded media file path: {media_file_path}")

            file_size = os.path.getsize(media_file_path)
            logging.info(f"Downloaded media file size: {file_size} bytes")
            if file_size > 0:
                bot.send_message(message.chat.id, "Media saved successfully.",reply_markup=back_keyboard())
                if latest_post_id is None:
                    latest_post_id = save_post_to_db(media_file_path, current_caption, current_buttons, current_media_type)
                else:
                    update_post_in_db(latest_post_id, media_file_path, current_caption, current_buttons, current_media_type)
                preview_message(message.chat.id)  
            else:
                bot.send_message(message.chat.id, "Failed to save media. The file is empty.",reply_markup=back_keyboard())
                os.remove(media_file_path)  
    else:
        bot.send_message(message.chat.id, "Invalid media type. Please send a photo, video, or document.",reply_markup=back_keyboard())

def handle_caption(message):
    global current_caption, latest_post_id
    current_caption = message.text
    bot.send_message(message.chat.id, "Caption saved successfully.",reply_markup=back_keyboard())
    if latest_post_id is not None:
        
        media_path, _, _, _ = load_post_from_db(latest_post_id)
        update_post_in_db(latest_post_id, media_path, current_caption, current_buttons, current_media_type)
    preview_message(message.chat.id)  

def handle_add_link_button(message):
    global current_buttons, latest_post_id
    try:
        rows = message.text.split('\n')
        for row in rows:
            buttons = row.split('|')
            for button in buttons:
                text, url = button.split('-')
                text = text.strip()
                url = url.strip()
                if is_valid_url(url):
                    current_buttons.append({'text': text, 'url': url})
                else:
                    bot.send_message(message.chat.id, f"Invalid URL: {url}. Please send the button text and a valid URL in the format: text - url", reply_markup=back_keyboard())
                    bot.register_next_step_handler(message, handle_add_link_button)
                    return
        bot.send_message(message.chat.id, "Buttons added successfully.", reply_markup=back_keyboard())
        if latest_post_id is not None:
            media_path, _, _, _ = load_post_from_db(latest_post_id)
            update_post_in_db(latest_post_id, media_path, current_caption, current_buttons, current_media_type)
        preview_message(message.chat.id)  
    except ValueError:
        bot.send_message(message.chat.id, "Invalid format. Please send the button text and URL in the format: text - url", reply_markup=back_keyboard())
        bot.register_next_step_handler(message, handle_add_link_button)

def handle_edit_link_button(message):
    global current_buttons, latest_post_id
    try:
        text, url = message.text.split('-')
        text = text.strip()  
        url = url.strip()  
        if is_valid_url(url):
            for button in current_buttons:
                if button['text'] == text:
                    button['url'] = url
                    bot.send_message(message.chat.id, "Button edited successfully.", reply_markup=back_keyboard())
                    if latest_post_id is not None:
                        media_path, _, _, _ = load_post_from_db(latest_post_id)
                        update_post_in_db(latest_post_id, media_path, current_caption, current_buttons, current_media_type)
                    preview_message(message.chat.id)  
                    return
            bot.send_message(message.chat.id, "Button not found.", reply_markup=back_keyboard())
        else:
            bot.send_message(message.chat.id, "Invalid URL. Please send the button text and a valid URL in the format: text - url", reply_markup=back_keyboard())
            bot.register_next_step_handler(message, handle_edit_link_button)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid format. Please send the button text and new URL in the format: text - url", reply_markup=back_keyboard())
        bot.register_next_step_handler(message, handle_edit_link_button)

def handle_delete_link_button(message):
    global current_buttons, latest_post_id
    text = message.text
    current_buttons = [button for button in current_buttons if button['text'] != text]
    bot.send_message(message.chat.id, "Button deleted successfully.",reply_markup=back_keyboard())
    if latest_post_id is not None:
        media_path, _, _, _ = load_post_from_db(latest_post_id)
        update_post_in_db(latest_post_id, media_path, current_caption, current_buttons, current_media_type)
    preview_message(message.chat.id)  

def preview_message(chat_id):
    inline_keyboard = types.InlineKeyboardMarkup()
    for button in current_buttons:
        inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], url=button['url']))
    
    # Add the "Edit Post" button
    inline_keyboard.add(types.InlineKeyboardButton(text="Edit Post", callback_data="edit_post"))

    inline_keyboard.add(types.InlineKeyboardButton(text="Send Broadcast", callback_data="broadcast_send_broadcast"))
    
    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel8"))

    media_file_pattern = f'{media_broadcast_path}/media_{current_media_number}.*'
    media_files = glob.glob(media_file_pattern)
    if media_files:
        media_file_path = media_files[0] 
        logging.info(f"Media path: {media_file_path}")
        if os.path.getsize(media_file_path) > 0:
            with open(media_file_path, 'rb') as media:
                if current_media_type == 'photo':
                    bot.send_photo(chat_id, media, caption=current_caption, reply_markup=inline_keyboard)
                elif current_media_type == 'video':
                    bot.send_video(chat_id, media, caption=current_caption, reply_markup=inline_keyboard)
                elif current_media_type == 'document':
                    bot.send_document(chat_id, media, caption=current_caption, reply_markup=inline_keyboard)
        else:
            bot.send_message(chat_id, "Failed to preview message. The media file is empty or does not exist.", reply_markup=back_keyboard())
            if current_caption:
                bot.send_message(chat_id, current_caption, reply_markup=inline_keyboard)
    else:
        bot.send_message(chat_id, "Failed to preview message. The media file does not exist.", reply_markup=back_keyboard())
        if current_caption:
            bot.send_message(chat_id, current_caption, reply_markup=inline_keyboard)

def send_broadcast(chat_id):
    global latest_post_id, successful_broadcast_count, failed_broadcast_count
    if latest_post_id is None:
        bot.send_message(chat_id, "No post available to broadcast.", reply_markup=back_keyboard())
        return

    post = load_post_from_db(latest_post_id)
    if not post:
        bot.send_message(chat_id, "Failed to send broadcast. Post not found.", reply_markup=back_keyboard())
        return

    media_path, caption, buttons, media_type = post
    if not media_path:
        bot.send_message(chat_id, "Failed to send broadcast. Media path is not set.", reply_markup=back_keyboard())
        return

    chat_ids = load_user_chat_ids()
    logging.info(f"Broadcasting to chat IDs: {chat_ids}")
    inline_keyboard = types.InlineKeyboardMarkup()
    for button in buttons:
        inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], url=button['url']))
    
    media_path = media_path.replace("\\", "/")
    logging.info(f"Formatted media path: {media_path}")

    if os.path.exists(media_path):
       file_size = os.path.getsize(media_path)
       logging.info(f"Media file size: {file_size} bytes")
       if file_size > 0:
           with open(media_path, 'rb') as media:
               media_content = media.read()
               logging.info(f"Media content size: {len(media_content)} bytes")
               if len(media_content) > 0:
                for user_id in chat_ids:
                    try:
                        if media_type == 'photo':
                            bot.send_photo(user_id, media_content, caption=caption, reply_markup=inline_keyboard)
                            successful_broadcast_count += 1  
                        elif media_type == 'video':
                            bot.send_video(user_id, media_content, caption=caption, reply_markup=inline_keyboard)
                            successful_broadcast_count += 1 
                        elif media_type == 'document':
                            bot.send_document(user_id, media_content, caption=caption, reply_markup=inline_keyboard)
                            successful_broadcast_count += 1  
                    except Exception as e:
                        logging.error(f"Failed to send broadcast to {user_id}: {e}")
                        failed_broadcast_count += 1  
                bot.send_message(chat_id, "Broadcast message sent to all subscribers. Use the button below to go back to main menu.", reply_markup=back_keyboard())
                send_broadcast_report(chat_id)  
               else:
                logging.error("Failed to send broadcast. The media file content is empty.")
                bot.send_message(chat_id, "Failed to send broadcast. The media file content is empty.", reply_markup=back_keyboard())
                if caption:
                    for user_id in chat_ids:
                        try:
                            bot.send_message(user_id, caption, reply_markup=inline_keyboard)
                            successful_broadcast_count += 1  
                        except Exception as e:
                            logging.error(f"Failed to send caption to {user_id}: {e}")
                            failed_broadcast_count += 1  
                bot.send_message(chat_id, "Broadcast message sent to all subscribers.", reply_markup=back_keyboard())
                send_broadcast_report(chat_id)  
       else:
            logging.error("Failed to send broadcast. The media file is empty.")
            bot.send_message(chat_id, "Failed to send broadcast. The media file is empty.", reply_markup=back_keyboard())
            if caption:
                for user_id in chat_ids:
                    try:
                        bot.send_message(user_id, caption, reply_markup=inline_keyboard)
                        successful_broadcast_count += 1  
                    except Exception as e:
                        logging.error(f"Failed to send caption to {user_id}: {e}")
                        failed_broadcast_count += 1  
            bot.send_message(chat_id, "Broadcast message sent to all subscribers.", reply_markup=back_keyboard())
    else:
        logging.error("Failed to send broadcast. The media file does not exist.")
        bot.send_message(chat_id, "Failed to send broadcast. The media file does not exist.", reply_markup=back_keyboard())
        if caption:
            for user_id in chat_ids:
                try:
                    bot.send_message(user_id, caption, reply_markup=inline_keyboard)
                    successful_broadcast_count += 1  
                except Exception as e:
                    logging.error(f"Failed to send caption to {user_id}: {e}")
                    failed_broadcast_count += 1  
        bot.send_message(chat_id, "Broadcast message sent to all subscribers.", reply_markup=back_keyboard())
    latest_post_id = None  

@bot.callback_query_handler(func=lambda call: call.data == "cancel8")
def handle_cancel8_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    bot.delete_message(chat_id, message_id)