import os
import sqlite3
import json
import logging
import datetime
import threading
import telebot
from telebot import types
from config import bot, media_path, bot_owner_id

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the config file
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def read_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            return json.load(file)
    else:
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

def write_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

def get_admin_ids():
    config = read_config()
    return config.get('admin_ids', [])

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Initialize the database
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def init_db_channel():
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_path TEXT,
                caption TEXT,
                links TEXT
            )
        ''')
        conn.commit()
        conn.close()

def init_db_scheduled_posts():
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            chat_id INTEGER,
            user_id INTEGER,
            scheduled_time TEXT,
            media_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def add_media_id_column():
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(scheduled_posts)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'media_id' not in columns:
        cursor.execute("ALTER TABLE scheduled_posts ADD COLUMN media_id INTEGER")
    conn.commit()
    conn.close()


def save_post_media_channel(media_file_path):
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO post_media (media_path) VALUES (?)', (media_file_path,))
    conn.commit()
    conn.close()

# Initialize the databases and add the column
init_db_channel()
init_db_scheduled_posts()
add_media_id_column()

def channel_post_menu(bot, call_or_message):
    if isinstance(call_or_message, types.CallbackQuery):
        chat_id = call_or_message.message.chat.id
        message_id = call_or_message.message.message_id
    else:
        chat_id = call_or_message.chat.id
        message_id = call_or_message.message_id

    # Create the new inline keyboard
    inline_keyboard = types.InlineKeyboardMarkup()
    buttons = [
        ("Add Channel", "add_channel_list"),
        ("Delete Channel", "delete_channel_list"),
        ("Add Post Media", "add_post8_media"),
        ("Delete Post Media", "delete_post8_media"),
        ("Add Post Caption", "add_post8_caption"),
        ("Edit Post Caption", "edit_post8_caption"),
        ("Add Post Link", "add_post8_link"),
        ("Edit Post Link", "edit_post8_link"),
        ("Delete Post Link", "delete_post8_link"),
        ("Perview Post Media", "perview_post8_media"),
        ("Cancel", "cancel8")
    ]
    
    # Add buttons to the inline keyboard
    inline_keyboard.row(
        types.InlineKeyboardButton(text="Add Channel", callback_data="add_channel_list"),
        types.InlineKeyboardButton(text="Delete Channel", callback_data="delete_channel_list")
    )
    inline_keyboard.add(types.InlineKeyboardButton(text="Add Post Media", callback_data="add_post8_media"))
    inline_keyboard.row(
        types.InlineKeyboardButton(text="Delete Post Media", callback_data="delete_post8_media"),
        types.InlineKeyboardButton(text="Add Post Caption", callback_data="add_post8_caption"),
        types.InlineKeyboardButton(text="Edit Post Caption", callback_data="edit_post8_caption")
    )
    inline_keyboard.row(
        types.InlineKeyboardButton(text="Add Post Link", callback_data="add_post8_link"),
        types.InlineKeyboardButton(text="Edit Post Link", callback_data="edit_post8_link"),
        types.InlineKeyboardButton(text="Delete Post Link", callback_data="delete_post8_link")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Perview Post Media", callback_data="perview_post8_media")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Perview Schedule Post", callback_data="perview3_schedule9_post8")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Cancel", callback_data="cancel8")
    )
    
    # Check if the message has text
    if isinstance(call_or_message, types.CallbackQuery):
        if call_or_message.message.text:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Channel Post Menu", reply_markup=inline_keyboard)
        else:
            bot.send_message(chat_id=chat_id, text="Channel Post Menu", reply_markup=inline_keyboard)
    else:
        bot.send_message(chat_id=chat_id, text="Channel Post Menu", reply_markup=inline_keyboard)

# Atur fungsi menambahkna media ke postingan
def handle_add_post_media_channel(bot, call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Please send the media (photo, video, or GIF) you want to add.")
    bot.register_next_step_handler_by_chat_id(chat_id, save_post_media_channel)

def save_post_media_channel(message):
    chat_id = message.chat.id
    media_file_path = get_next_media_filename()

    if message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        media_file_path += '.jpg'
    elif message.content_type == 'video':
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        media_file_path += '.mp4'
    elif message.content_type == 'document' and message.document.mime_type in ['image/gif', 'video/mp4']:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        media_file_path += '.gif' if message.document.mime_type == 'image/gif' else '.mp4'
    else:
        bot.send_message(chat_id, "Unsupported media type. Please send a photo, video, or GIF.")
        return

    with open(media_file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    # Save media path to the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO post_media (media_path) VALUES (?)', (media_file_path,))
    conn.commit()
    conn.close()

    # Send confirmation message
    bot.send_message(chat_id, "Media saved successfully.")

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Edit Post", callback_data="edit_channel_post"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Send Post", callback_data="send_post8"))

    # Send the media with inline buttons
    if message.content_type == 'photo':
        bot.send_photo(chat_id, photo=open(media_file_path, 'rb'), reply_markup=inline_keyboard)
    elif message.content_type == 'video':
        bot.send_video(chat_id, video=open(media_file_path, 'rb'), reply_markup=inline_keyboard)
    elif message.content_type == 'document' and message.document.mime_type in ['image/gif', 'video/mp4']:
        bot.send_document(chat_id, document=open(media_file_path, 'rb'), reply_markup=inline_keyboard)

# FUNGSI ADD CHANNEL
@bot.callback_query_handler(func=lambda call: call.data == "add_channel_list")
def handle_add_channel_list(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    # Check if the user is the owner or an admin
    if user_id == bot_owner_id or user_id in get_admin_ids():
        msg = bot.send_message(chat_id, "Please send the Telegram channel usernames to add, separated by commas.")
        bot.register_next_step_handler(msg, save_channel_usernames)
    else:
        bot.send_message(chat_id, "You are not authorized to perform this action.")

def save_channel_usernames(message):
    chat_id = message.chat.id
    usernames = message.text.split(',')

    config = read_config()
    if 'channels' not in config:
        config['channels'] = []

    existing_channels = []
    new_channels = []
    new_channel_names = []

    for username in usernames:
        username = username.strip()
        if username in config['channels']:
            existing_channels.append(username)
        else:
            try:
                channel_info = bot.get_chat(username)
                channel_name = channel_info.title
                new_channels.append(username)
                new_channel_names.append(channel_name)
                config['channels'].append(username)
            except Exception as e:
                bot.send_message(chat_id, f"Failed to get information for {username}: {e}")

    write_config(config)

    if existing_channels:
        inline_keyboard = types.InlineKeyboardMarkup()
        inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel8"))
        bot.send_message(chat_id, f"The following channels already exist: {', '.join(existing_channels)}. Please send different usernames.", reply_markup=inline_keyboard)
        msg = bot.send_message(chat_id, "Please send the Telegram channel usernames to add, separated by commas.")
        bot.register_next_step_handler(msg, save_channel_usernames)
    else:
        bot.send_message(chat_id, f"The following channels have been saved: {', '.join(new_channel_names)}")
        channel_post_menu(bot, message)

@bot.callback_query_handler(func=lambda call: call.data == "edit_channel_post")
def handle_edit_channel_post(call):
    channel_post_menu(bot, call)

@bot.callback_query_handler(func=lambda call: call.data == "add_post8_caption")
def handle_add_post_caption_callback_channel(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Please send the caption you want to add.")
    bot.register_next_step_handler_by_chat_id(chat_id, save_post_caption_channel)

def save_post_caption_channel(message):
    chat_id = message.chat.id
    caption = message.text

    # Save caption to the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE post_media SET caption = ? WHERE id = (SELECT MAX(id) FROM post_media)', (caption,))
    conn.commit()

    # Retrieve the latest media path from the database
    cursor.execute('SELECT media_path FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    result = cursor.fetchone()
    conn.close()

    if result is None:
        bot.send_message(chat_id, "No media found to update the caption.")
        return

    media_file_path = result[0]

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Edit Post", callback_data="edit_channel_post"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Send Post", callback_data="send_post8"))

    # Send the media with the caption and inline buttons
    send_media_with_caption_and_links_channel(chat_id, media_file_path, caption, inline_keyboard)

def save_post_link_channel(message):
    chat_id = message.chat.id
    links = message.text

    # Save links to the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE post_media SET links = ? WHERE id = (SELECT MAX(id) FROM post_media)', (links,))
    conn.commit()
    conn.close()

# Retrieve the latest media path and caption from the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT media_path, caption FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    result = cursor.fetchone()
    conn.close()

    if result is None:
        bot.send_message(chat_id, "No media found to update the links.")
        return

    media_file_path, caption = result

    inline_keyboard = types.InlineKeyboardMarkup()

    # Parse the links and add them to the inline keyboard
    rows = links.split('\n')
    for row in rows:
        buttons = row.split('|')
        button_row = []
        for button in buttons:
            if '-' in button:
                text, url = button.split('-')
                button_row.append(types.InlineKeyboardButton(text=text.strip(), url=url.strip()))
            else:
                bot.send_message(chat_id, f"Invalid format for button: {button}. Expected format: Text - url")
                return
        inline_keyboard.row(*button_row)

    inline_keyboard.add(types.InlineKeyboardButton(text="Edit Post", callback_data="edit_channel_post"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Send Post", callback_data="send_post8"))

    # Send the media with the caption and inline buttons
    send_media_with_caption_and_links_channel(chat_id, media_file_path, caption, inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "add_post8_link")
def handle_add_post_link_callback_channel(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Please send the button text and URL in the format: Text - url | Text - url")
    bot.register_next_step_handler_by_chat_id(chat_id, save_post_link_channel)

def save_post_link_channel(message):
    chat_id = message.chat.id
    links = message.text

    # Save links to the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE post_media SET links = ? WHERE id = (SELECT MAX(id) FROM post_media)', (links,))
    conn.commit()
    conn.close()

# Retrieve the latest media path and caption from the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT media_path, caption FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    result = cursor.fetchone()
    conn.close()

    if result is None:
        bot.send_message(chat_id, "No media found to update the links.")
        return

    media_file_path, caption = result

    inline_keyboard = types.InlineKeyboardMarkup()

    # Parse the links and add them to the inline keyboard
    rows = links.split('\n')
    for row in rows:
        buttons = row.split('|')
        button_row = []
        for button in buttons:
            if '-' in button:
                text, url = button.split('-')
                button_row.append(types.InlineKeyboardButton(text=text.strip(), url=url.strip()))
            else:
                bot.send_message(chat_id, f"Invalid format for button: {button}. Expected format: Text - url")
                return
        inline_keyboard.row(*button_row)

    inline_keyboard.add(types.InlineKeyboardButton(text="Edit Post", callback_data="edit_channel_post"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Send Post", callback_data="send_post8"))

    # Send the media with the caption and inline buttons
    send_media_with_caption_and_links_channel(chat_id, media_file_path, caption, inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "edit_post8_link")
def handle_edit_post3_link_callback_channel(call):
    chat_id = call.message.chat.id

    # Retrieve the latest links from the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT links FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    result = cursor.fetchone()
    conn.close()

    if result is None or result[0] is None:
        bot.send_message(chat_id, "No links found to edit.")
        return

    links = result[0]

    # Parse the links and create inline buttons for each link
    inline_keyboard = types.InlineKeyboardMarkup()
    rows = links.split('\n')
    for row in rows:
        buttons = row.split('|')
        for button in buttons:
            if '-' in button:
                text, url = button.split('-')
                inline_keyboard.add(types.InlineKeyboardButton(text=text.strip(), callback_data=f"edit_post3_link{text.strip()}"))

    bot.send_message(chat_id, "Select the link you want to edit:", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_post3_link"))
def handle_select_link_to_edit_channel(call):
    chat_id = call.message.chat.id
    link_text = call.data[len("edit_post3_link"):]

    bot.send_message(chat_id, f"Please send the new URL for the link '{link_text}':")
    bot.register_next_step_handler_by_chat_id(chat_id, update_post_link_channel, link_text)

def update_post_link_channel(message, link_text):
    chat_id = message.chat.id
    new_url = message.text

    # Retrieve the latest links from the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT links FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    result = cursor.fetchone()
    conn.close()

    if result is None or result[0] is None:
        bot.send_message(chat_id, "No links found to update.")
        return

    links = result[0]

    # Update the specific link
    updated_links = []
    rows = links.split('\n')
    for row in rows:
        buttons = row.split('|')
        updated_row = []
        for button in buttons:
            if '-' in button:
                text, url = button.split('-')
                if text.strip() == link_text:
                    updated_row.append(f"{text.strip()} - {new_url.strip()}")
                else:
                    updated_row.append(button)
        updated_links.append(' | '.join(updated_row))
    updated_links_str = '\n'.join(updated_links)

    # Save the updated links to the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE post_media SET links = ? WHERE id = (SELECT MAX(id) FROM post_media)', (updated_links_str,))
    conn.commit()
    conn.close()

    bot.send_message(chat_id, f"Link for '{link_text}' has been updated to '{new_url}'.")

    # Retrieve the latest media path and caption from the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT media_path, caption FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    result = cursor.fetchone()
    conn.close()


    if result is None:
        bot.send_message(chat_id, "No media found to update the links.")
        return

    media_file_path, caption = result

    inline_keyboard = types.InlineKeyboardMarkup()

    # Parse the updated links and add them to the inline keyboard
    rows = updated_links_str.split('\n')
    for row in rows:
        buttons = row.split('|')
        button_row = []
        for button in buttons:
            if '-' in button:
                text, url = button.split('-')
                button_row.append(types.InlineKeyboardButton(text=text.strip(), url=url.strip()))
        inline_keyboard.row(*button_row)

    inline_keyboard.add(types.InlineKeyboardButton(text="Edit Post", callback_data="edit_channel_post"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Send Post", callback_data="send_post8"))

    # Send the media with the caption and updated inline buttons
    send_media_with_caption_and_links_channel(chat_id, media_file_path, caption, inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "delete_post8_link")
def handle_delete_post3_link_callback_channel(call):
    chat_id = call.message.chat.id

    # Retrieve the latest links from the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT links FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    result = cursor.fetchone()
    conn.close()

    if result is None or result[0] is None:
        bot.send_message(chat_id, "No links found to delete.")
        return

    links = result[0]

    # Parse the links and create inline buttons for each link
    inline_keyboard = types.InlineKeyboardMarkup()
    rows = links.split('\n')
    for row in rows:
        buttons = row.split('|')
        for button in buttons:
            if '-' in button:
                text, url = button.split('-')
                inline_keyboard.add(types.InlineKeyboardButton(text=text.strip(), callback_data=f"delete_post_link_{text.strip()}"))

    bot.send_message(chat_id, "Select the link you want to delete:", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_post_link_"))
def handle_select_link_to_delete_channel(call):
    chat_id = call.message.chat.id
    link_text = call.data[len("delete_post_link_"):]

    # Retrieve the latest links from the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT links FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    links = cursor.fetchone()[0]
    conn.close()

    # Remove the selected link
    updated_links = []
    rows = links.split('\n')
    for row in rows:
        buttons = row.split('|')
        updated_row = [button for button in buttons if not button.strip().startswith(link_text)]
        if updated_row:
            updated_links.append(' | '.join(updated_row))
    updated_links_str = '\n'.join(updated_links)

    # Save the updated links to the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE post_media SET links = ? WHERE id = (SELECT MAX(id) FROM post_media)', (updated_links_str,))
    conn.commit()
    conn.close()

    if not updated_links_str.strip():
        bot.send_message(chat_id, "No links left to delete.")
        # Retrieve the latest media path and caption from the database
        db_dir = os.path.dirname(__file__)
        db_path = os.path.join(db_dir, 'postmedia.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT media_path, caption FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
        media_file_path, caption = cursor.fetchone()
        conn.close()

        inline_keyboard = types.InlineKeyboardMarkup()
        inline_keyboard.add(types.InlineKeyboardButton(text="Edit Post", callback_data="edit_channel_post"))
        inline_keyboard.add(types.InlineKeyboardButton(text="Send Post", callback_data="send_post8"))

        # Send the media with the caption and updated inline buttons
        send_media_with_caption_and_links_channel(chat_id, media_file_path, caption, inline_keyboard)
        return

    bot.send_message(chat_id, f"Link '{link_text}' has been deleted.")

    # Retrieve the latest media path and caption from the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT media_path, caption FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    media_file_path, caption = cursor.fetchone()
    conn.close()

    inline_keyboard = types.InlineKeyboardMarkup()

    # Parse the updated links and add them to the inline keyboard
    rows = updated_links_str.split('\n')
    for row in rows:
        buttons = row.split('|')
        button_row = []
        for button in buttons:
            if '-' in button:
                text, url = button.split('-')
                button_row.append(types.InlineKeyboardButton(text=text.strip(), url=url.strip()))
        inline_keyboard.row(*button_row)

    inline_keyboard.add(types.InlineKeyboardButton(text="Edit Post", callback_data="edit_channel_post"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Send Post", callback_data="send_post8"))

    # Send the media with the caption and updated inline buttons
    send_media_with_caption_and_links_channel(chat_id, media_file_path, caption, inline_keyboard)

#FUNGSI CANCEL
@bot.callback_query_handler(func=lambda call: call.data == "cancel8")
def handle_cancel8_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Delete the previous menu message
    bot.delete_message(chat_id, message_id)

#FUNGSI PERVIEW
@bot.callback_query_handler(func=lambda call: call.data == "perview_post8_media")
def handle_perview_post3_media_callback(call):
    chat_id = call.message.chat.id

    # Retrieve the latest media path, caption, and links from the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT media_path, caption, links FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    result = cursor.fetchone()
    conn.close()

    if result is None:
        bot.send_message(chat_id, "No post found to preview.")
        return

    media_file_path, caption, links = result

    inline_keyboard = types.InlineKeyboardMarkup()

    # Parse the links and add them to the inline keyboard
    if links:
        rows = links.split('\n')
        for row in rows:
            buttons = row.split('|')
            button_row = []
            for button in buttons:
                if '-' in button:
                    text, url = button.split('-')
                    button_row.append(types.InlineKeyboardButton(text=text.strip(), url=url.strip()))
            inline_keyboard.row(*button_row)

    inline_keyboard.add(types.InlineKeyboardButton(text="Edit Post", callback_data="edit_channel_post"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Send Post", callback_data="send_post8"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel8"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Delete Post Media", callback_data="delete_post8_media"))

    # Check if only caption should be sent
    if not media_file_path and not inline_keyboard.keyboard:
        bot.send_message(chat_id, text=caption)
    else:
        # Send the media with the caption and inline buttons
        send_media_with_caption_and_links_channel(chat_id, media_file_path, caption, inline_keyboard)

def send_media_with_caption_and_links_channel(chat_id, media_file_path=None, caption="", inline_keyboard=None):
    # Send the media with the caption and inline buttons
    if media_file_path:
        if media_file_path.endswith('.jpg'):
            bot.send_photo(chat_id, photo=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
        elif media_file_path.endswith('.mp4'):
            bot.send_video(chat_id, video=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
        elif media_file_path.endswith('.gif'):
            bot.send_document(chat_id, document=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
    else:
        bot.send_message(chat_id, text=caption, reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "delete_post8_media")
def handle_delete_post8_media(call):
    chat_id = call.message.chat.id

    # Retrieve the latest caption and links from the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT caption, links FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    result = cursor.fetchone()

    if result is None:
        bot.send_message(chat_id, "No post found to delete media from.")
        conn.close()
        return

    caption, links = result

    # Update the database to remove the media path
    cursor.execute('UPDATE post_media SET media_path = NULL WHERE id = (SELECT MAX(id) FROM post_media)')
    conn.commit()
    conn.close()

    inline_keyboard = types.InlineKeyboardMarkup()

    # Parse the links and add them to the inline keyboard
    if links:
        rows = links.split('\n')
        for row in rows:
            buttons = row.split('|')
            button_row = []
            for button in buttons:
                if '-' in button:
                    text, url = button.split('-')
                    button_row.append(types.InlineKeyboardButton(text=text.strip(), url=url.strip()))
            inline_keyboard.row(*button_row)

    inline_keyboard.add(types.InlineKeyboardButton(text="Edit Post", callback_data="edit_channel_post"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Send Post", callback_data="send_post8"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel8"))

    # Check if only caption should be sent
    if not links:
        bot.send_message(chat_id, text=caption)
    else:
        # Send the caption with the inline buttons
        bot.send_message(chat_id, text=caption, reply_markup=inline_keyboard)

def send_media_with_caption_and_links_channel(chat_id, media_file_path=None, caption="", inline_keyboard=None):
    # Send the media with the caption and inline buttons
    if media_file_path:
        if media_file_path.endswith('.jpg'):
            bot.send_photo(chat_id, photo=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
        elif media_file_path.endswith('.mp4'):
            bot.send_video(chat_id, video=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
        elif media_file_path.endswith('.gif'):
            bot.send_document(chat_id, document=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
    else:
        bot.send_message(chat_id, text=caption, reply_markup=inline_keyboard)

#FUNGSI DELET CHANNEL
@bot.callback_query_handler(func=lambda call: call.data == "delete_channel_list")
def handle_delete_channel_list(call):
    chat_id = call.message.chat.id

    config = read_config()
    channels = config.get('channels', [])

    if not channels:
        bot.send_message(chat_id, "No channels found to delete.")
        return

    inline_keyboard = types.InlineKeyboardMarkup()
    for username in channels:
        try:
            channel_info = bot.get_chat(username)
            channel_name = channel_info.title
            inline_keyboard.add(types.InlineKeyboardButton(text=channel_name, callback_data=f"delete_channel_{username}"))
        except Exception as e:
            bot.send_message(chat_id, f"Failed to get information for {username}: {e}")
    inline_keyboard.add(types.InlineKeyboardButton(text="Return To Menu", callback_data="return3_menu"))

    bot.send_message(chat_id, "Select the channel you want to delete:", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_channel_"))
def handle_delete_channel(call):
    chat_id = call.message.chat.id
    channel_to_delete = call.data[len("delete_channel_"):]

    try:
        config = read_config()
        channels = config.get('channels', [])

        if channel_to_delete in channels:
            channels.remove(channel_to_delete)
            config['channels'] = channels
            write_config(config)
            bot.send_message(chat_id, f"The channel '{channel_to_delete}' has been deleted from the list.")
            logging.info(f"Channel '{channel_to_delete}' deleted from the list.")
        else:
            bot.send_message(chat_id, f"The channel '{channel_to_delete}' was not found in the list.")
            logging.warning(f"Channel '{channel_to_delete}' not found in the list.")

        # Display the updated list of channels
        if channels:
            inline_keyboard = types.InlineKeyboardMarkup()
            for channel in channels:
                inline_keyboard.add(types.InlineKeyboardButton(text=channel, callback_data=f"delete_channel_{channel}"))
            inline_keyboard.add(types.InlineKeyboardButton(text="Return To Menu", callback_data="return3_menu"))
            bot.send_message(chat_id, "Select the channel you want to delete:", reply_markup=inline_keyboard)
        else:
            bot.send_message(chat_id, "No channels left to delete.")
            channel_post_menu(bot, call)
    except Exception as e:
        bot.send_message(chat_id, "An error occurred while deleting the channel.")
        logging.error(f"Error deleting channel '{channel_to_delete}': {e}")

@bot.callback_query_handler(func=lambda call: call.data == "return3_menu")
def handle_return3_menu(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # Send the "Channel Post Menu"
    channel_post_menu(bot, call)

#FUNGSI TOMBOL SEND POST / SEND POST SELECT CHANNEL LIST
@bot.callback_query_handler(func=lambda call: call.data == "send_post8")
def handle_send_post(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    logging.info(f"User {user_id} initiated sending a post.")

    config = read_config()
    channels = config.get('channels', [])

    if not channels:
        bot.send_message(chat_id, "No channels found to send the post.")
        logging.info(f"User {user_id} found no channels to send the post.")
        return

    # Create the new inline keyboard
    inline_keyboard = types.InlineKeyboardMarkup()
    for username in channels:
        try:
            channel_info = bot.get_chat(username)
            channel_name = channel_info.title
            inline_keyboard.add(types.InlineKeyboardButton(text=channel_name, callback_data=f"send_post_to_{username}"))
        except Exception as e:
            bot.send_message(chat_id, f"Failed to get information for {username}: {e}")
            logging.error(f"Failed to get information for {username}: {e}")

    # Add "Send To All" button
    inline_keyboard.add(types.InlineKeyboardButton(text="Send To All", callback_data="send_post3_to_all"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel8"))

    # Send the message with inline buttons
    bot.send_message(chat_id, "Select the channel you want to send the post to:", reply_markup=inline_keyboard)
    logging.info(f"User {user_id} is selecting a channel to send the post.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("send_post_to_"))
def handle_send_post_to_channel(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.data[len("send_post_to_"):]

    try:
        channel_info = bot.get_chat(username)
        channel_name = channel_info.title
    except Exception as e:
        bot.send_message(chat_id, f"Failed to get information for {username}: {e}")
        logging.error(f"Failed to get information for {username}: {e}")
        return

    # Create the new inline keyboard
    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.row(
        types.InlineKeyboardButton(text="Send Now", callback_data=f"send_now_{username}"),
        types.InlineKeyboardButton(text="Enqueue", callback_data=f"enqueue_{username}")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Cancel", callback_data="cancel8")
    )

    # Send the message with inline buttons
    bot.send_message(chat_id, f"When do you want to send this post to {channel_name}?", reply_markup=inline_keyboard)
    logging.info(f"User {user_id} is deciding when to send the post to {channel_name}.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("send_now_"))
def handle_send_now(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.data[len("send_now_"):]

    # Retrieve the latest media path, caption, and links from the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT media_path, caption, links FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    result = cursor.fetchone()
    conn.close()

    if result is None:
        bot.send_message(chat_id, "No post found to send.")
        logging.info(f"User {user_id} found no post to send.")
        return

    media_file_path, caption, links = result

    # Send the media with the caption and links to the selected channel
    inline_keyboard = types.InlineKeyboardMarkup()
    if links:
        rows = links.split('\n')
        for row in rows:
            buttons = row.split('|')
            button_row = []
            for button in buttons:
                if '-' in button:
                    text, url = button.split('-')
                    button_row.append(types.InlineKeyboardButton(text=text.strip(), url=url.strip()))
            inline_keyboard.row(*button_row)

    if media_file_path:
        if media_file_path.endswith('.jpg'):
            bot.send_photo(username, photo=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
        elif media_file_path.endswith('.mp4'):
            bot.send_video(username, video=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
        elif media_file_path.endswith('.gif'):
            bot.send_document(username, document=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
    else:
        bot.send_message(username, text=caption, reply_markup=inline_keyboard)

    # Fetch the channel name
    try:
        channel_info = bot.get_chat(username)
        channel_name = channel_info.title
    except Exception as e:
        bot.send_message(chat_id, f"Failed to get information for {username}: {e}")
        logging.error(f"Failed to get information for {username}: {e}")
        return

    # Notify that the post has been sent with "Return" button
    return_keyboard = types.InlineKeyboardMarkup()
    return_keyboard.add(types.InlineKeyboardButton(text="Return", callback_data="return3_to3_menu"))
    bot.send_message(chat_id, f"The post has been sent to {channel_name}.", reply_markup=return_keyboard)
    logging.info(f"User {user_id} sent the post to {channel_name}.")

@bot.callback_query_handler(func=lambda call: call.data == "return3_to3_menu")
def handle_return3_to3_menu(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    logging.info(f"User {user_id} returned to the channel post menu.")
    channel_post_menu(bot, call)

#FUNGSI ENQUEUE / SHECDULE POST
@bot.callback_query_handler(func=lambda call: call.data.startswith("enqueue_"))
def handle_enqueue(call):
    chat_id = call.message.chat.id
    username = call.data[len("enqueue_"):]
    
    bot.send_message(chat_id, "Please provide the scheduled time in the format: HH MM DD M (e.g., 18 00 12 1)")
    bot.register_next_step_handler_by_chat_id(chat_id, process_scheduled_time, username)

def process_scheduled_time(message, username):
    chat_id = message.chat.id
    user_id = message.from_user.id
    scheduled_time_str = message.text

    try:
        current_time = datetime.datetime.now()
        current_year = current_time.year
        scheduled_time = datetime.datetime.strptime(scheduled_time_str, "%H %M %d %m")
        scheduled_time = scheduled_time.replace(year=current_year)

        logging.info(f"Current time: {current_time}")
        logging.info(f"Scheduled time: {scheduled_time}")

        if scheduled_time <= current_time + datetime.timedelta(minutes=1):
            bot.send_message(chat_id, "The scheduled time must be at least 1 minute in the future. Please try again.")
            logging.info(f"User {user_id} provided an invalid scheduled time: {scheduled_time_str}")
            return

        # Retrieve the latest media ID from the database
        db_dir = os.path.dirname(__file__)
        db_path = os.path.join(db_dir, 'postmedia.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
        result = cursor.fetchone()
        conn.close()

        if result is None:
            bot.send_message(chat_id, "No media found to schedule.")
            logging.info(f"User {user_id} found no media to schedule.")
            return

        media_id = result[0]
        logging.info(f"Media ID retrieved: {media_id}")

        # Save the scheduled post to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO scheduled_posts (username, chat_id, user_id, scheduled_time, media_id) VALUES (?, ?, ?, ?, ?)',
                       (username, chat_id, user_id, scheduled_time_str, media_id))
        conn.commit()
        conn.close()

        # Schedule the post
        delay = (scheduled_time - current_time).total_seconds()
        logging.info(f"Scheduling post with delay: {delay} seconds")
        threading.Timer(delay, send_scheduled_post, args=[username, chat_id, user_id, scheduled_time_str, media_id]).start()

        bot.send_message(chat_id, f"The post has been scheduled for {scheduled_time.strftime('%H:%M %d-%m-%Y')}.")
        logging.info(f"User {user_id} scheduled a post for {scheduled_time.strftime('%Y-%m-%d %H:%M')} to {username}.")
        channel_post_menu(bot, message)
    except ValueError:
        bot.send_message(chat_id, "Invalid time format. Please provide the time in the format: HH MM DD M (e.g., 18 00 12 1)")
        logging.info(f"User {user_id} provided an invalid time format: {scheduled_time_str}")

def process_scheduled_time_all(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    scheduled_time_str = message.text

    try:
        current_time = datetime.datetime.now()
        current_year = current_time.year
        scheduled_time = datetime.datetime.strptime(scheduled_time_str, "%H %M %d %m")
        scheduled_time = scheduled_time.replace(year=current_year)

        logging.info(f"Current time: {current_time}")
        logging.info(f"Scheduled time: {scheduled_time}")

        if scheduled_time <= current_time + datetime.timedelta(minutes=1):
            bot.send_message(chat_id, "The scheduled time must be at least 1 minute in the future. Please try again.")
            logging.info(f"User {user_id} provided an invalid scheduled time: {scheduled_time_str}")
            return

        # Retrieve the latest media ID from the database
        db_dir = os.path.dirname(__file__)
        db_path = os.path.join(db_dir, 'postmedia.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
        result = cursor.fetchone()
        conn.close()

        if result is None:
            bot.send_message(chat_id, "No media found to schedule.")
            logging.info(f"User {user_id} found no media to schedule.")
            return

        media_id = result[0]
        logging.info(f"Media ID retrieved: {media_id}")

        config = read_config()
        channels = config.get('channels', [])

        if not channels:
            bot.send_message(chat_id, "No channels found to send the post.")
            logging.info(f"User {user_id} found no channels to send the post.")
            return

        # Save the scheduled post to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for username in channels:
            cursor.execute('INSERT INTO scheduled_posts (username, chat_id, user_id, scheduled_time, media_id) VALUES (?, ?, ?, ?, ?)',
                           (username, chat_id, user_id, scheduled_time_str, media_id))
        conn.commit()
        conn.close()

        for username in channels:
            try:
                delay = (scheduled_time - current_time).total_seconds()
                logging.info(f"Scheduling post for {username} with delay: {delay} seconds")
                threading.Timer(delay, send_scheduled_post, args=[username, chat_id, user_id, scheduled_time_str, media_id]).start()
                logging.info(f"User {user_id} scheduled a post for {scheduled_time.strftime('%Y-%m-%d %H:%M')} to {username}.")
            except Exception as e:
                logging.error(f"Failed to schedule post to {username}: {e}")
                bot.send_message(chat_id, f"Failed to schedule post to {username}: {e}")

        bot.send_message(chat_id, f"The post has been scheduled for {scheduled_time.strftime('%H:%M %d-%m-%Y')} to all channels.")
        channel_post_menu(bot, message)
    except ValueError:
        bot.send_message(chat_id, "Invalid time format. Please provide the time in the format: HH MM DD M (e.g., 18 00 12 1)")
        logging.info(f"User {user_id} provided an invalid time format: {scheduled_time_str}")

#FUNGSI SEND POST TO ALL
@bot.callback_query_handler(func=lambda call: call.data == "send_post3_to_all")
def handle_send_post3_to_all(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    # Create the new inline keyboard
    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.row(
        types.InlineKeyboardButton(text="Send Now", callback_data="send3_now_all"),
        types.InlineKeyboardButton(text="Enqueue", callback_data="enqueue3_all")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Cancel", callback_data="cancel8")
    )

    # Send the message with inline buttons
    bot.send_message(chat_id, "When do you want to send this post to all channels?", reply_markup=inline_keyboard)
    logging.info(f"User {user_id} is deciding when to send the post to all channels.")

@bot.callback_query_handler(func=lambda call: call.data == "send3_now_all")
def handle_send3_now_all(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    # Retrieve the latest media path, caption, and links from the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT media_path, caption, links FROM post_media WHERE id = (SELECT MAX(id) FROM post_media)')
    result = cursor.fetchone()
    conn.close()

    if result is None:
        bot.send_message(chat_id, "No post found to send.")
        logging.info(f"User {user_id} found no post to send.")
        return

    media_file_path, caption, links = result

    config = read_config()
    channels = config.get('channels', [])

    if not channels:
        bot.send_message(chat_id, "No channels found to send the post.")
        logging.info(f"User {user_id} found no channels to send the post.")
        return

    for username in channels:
        try:
            logging.info(f"Attempting to get information for channel: {username}")
            channel_info = bot.get_chat(username)
            channel_name = channel_info.title

            # Send the media with the caption and links to the selected channel
            inline_keyboard = types.InlineKeyboardMarkup()
            if links:
                rows = links.split('\n')
                for row in rows:
                    buttons = row.split('|')
                    button_row = []
                    for button in buttons:
                        if '-' in button:
                            text, url = button.split('-')
                            button_row.append(types.InlineKeyboardButton(text=text.strip(), url=url.strip()))
                    inline_keyboard.row(*button_row)

            if media_file_path.endswith('.jpg'):
                bot.send_photo(username, photo=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
            elif media_file_path.endswith('.mp4'):
                bot.send_video(username, video=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
            elif media_file_path.endswith('.gif'):
                bot.send_document(username, document=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)

            logging.info(f"User {user_id} sent the post to {channel_name}.")
        except telebot.apihelper.ApiException as e:
            if e.result.status_code == 400 and "chat not found" in e.result.text:
                logging.error(f"Failed to send post to {username}: chat not found.")
            else:
                logging.error(f"Failed to send post to {username}: {e}")
            bot.send_message(chat_id, f"Failed to send post to {username}: {e}")

    # Notify that the post has been sent to all channels with "Return" button
    return_keyboard = types.InlineKeyboardMarkup()
    return_keyboard.add(types.InlineKeyboardButton(text="Return", callback_data="return3_to3_menu"))
    bot.send_message(chat_id, "The post has been sent to all channels.", reply_markup=return_keyboard)
    logging.info(f"User {user_id} sent the post to all channels.")

@bot.callback_query_handler(func=lambda call: call.data == "enqueue3_all")
def handle_enqueue3_all(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    bot.send_message(chat_id, "Please provide the scheduled time in the format: HH MM DD M (e.g., 18 00 12 1)")
    bot.register_next_step_handler_by_chat_id(chat_id, process_scheduled_time_all)

# Define the send_scheduled_post function
def send_scheduled_post(username, chat_id, user_id, scheduled_time_str, media_id):
    logging.info(f"send_scheduled_post called with media_id: {media_id}")
    
    # Retrieve the media path, caption, and links from the database based on media_id
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT media_path, caption, links FROM post_media WHERE id = ?', (media_id,))
    result = cursor.fetchone()
    conn.close()

    if result is None:
        bot.send_message(chat_id, "No post found to send.")
        logging.info(f"User {user_id} found no post to send.")
        return

    media_file_path, caption, links = result

    # Send the media with the caption and links to the selected channel
    inline_keyboard = types.InlineKeyboardMarkup()
    if links:
        rows = links.split('\n')
        for row in rows:
            buttons = row.split('|')
            button_row = []
            for button in buttons:
                if '-' in button:
                    text, url = button.split('-')
                    button_row.append(types.InlineKeyboardButton(text=text.strip(), url=url.strip()))
            inline_keyboard.row(*button_row)

    if media_file_path:
        if media_file_path.endswith('.jpg'):
            bot.send_photo(username, photo=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
        elif media_file_path.endswith('.mp4'):
            bot.send_video(username, video=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
        elif media_file_path.endswith('.gif'):
            bot.send_document(username, document=open(media_file_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
    else:
        bot.send_message(username, text=caption, reply_markup=inline_keyboard)

    # Fetch the channel name
    try:
        channel_info = bot.get_chat(username)
        channel_name = channel_info.title
    except Exception as e:
        bot.send_message(chat_id, f"Failed to get information for {username}: {e}")
        logging.error(f"Failed to get information for {username}: {e}")
        return

    # Notify that the post has been sent with "Return" button
    return_keyboard = types.InlineKeyboardMarkup()
    success_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    bot.send_message(chat_id, f"The post has been sent to {channel_name} at {success_time}.", reply_markup=return_keyboard)
    
    # Log the success with timestamp
    logging.info(f"User {user_id} sent the post to {channel_name} at {success_time}.")

    # Remove the sent post from the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scheduled_posts WHERE username = ? AND chat_id = ? AND user_id = ? AND scheduled_time = ?',
                   (username, chat_id, user_id, scheduled_time_str))
    conn.commit()
    conn.close()

# Define the reload_scheduled_posts function
def reload_scheduled_posts():
    logging.info("reload_scheduled_posts called")
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT username, chat_id, user_id, scheduled_time, media_id FROM scheduled_posts')
    rows = cursor.fetchall()
    conn.close()

    current_time = datetime.datetime.now()
    skipped_logs = []
    for row in rows:
        username, chat_id, user_id, scheduled_time_str, media_id = row
        scheduled_time = datetime.datetime.strptime(scheduled_time_str, "%H %M %d %m")
        scheduled_time = scheduled_time.replace(year=current_time.year)
        if scheduled_time > current_time:
            delay = (scheduled_time - current_time).total_seconds()
            threading.Timer(delay, send_scheduled_post, args=[username, chat_id, user_id, scheduled_time_str, media_id]).start()
            logging.info(f"Reloaded scheduled post for {scheduled_time.strftime('%Y-%m-%d %H:%M')} to {username}.")
        else:
            skipped_logs.append(f"Scheduled time {scheduled_time} for {username} is in the past. Skipping.")

    # Log only the last 3 skipped posts
    for log in skipped_logs[-3:]:
        logging.warning(log)

# Ensure the send_scheduled_post function is defined before calling reload_scheduled_posts
if __name__ == "__main__":
    reload_scheduled_posts()

def get_next_media_filename():
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    media_base_path = media_path  # Ensure media_path is defined elsewhere in your code
    for i in range(1, 31):
        media_filename = f"media_post{i}_{today_str}"
        media_file_path = os.path.join(media_base_path, media_filename)
        if not os.path.exists(media_file_path + '.jpg') and not os.path.exists(media_file_path + '.mp4') and not os.path.exists(media_file_path + '.gif'):
            return media_file_path
    # If all 30 posts exist, overwrite the oldest one
    return os.path.join(media_base_path, f"media_post1_{today_str}")

#FUNGSI TOMBOL PERVIEW SCHEDULE POST
@bot.callback_query_handler(func=lambda call: call.data == "perview3_schedule9_post8")
def handle_preview3_scheduled9_posts8(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    logging.info(f"User {user_id} requested to preview scheduled posts.")
    
    # Retrieve scheduled posts from the database
    scheduled_posts = get_scheduled_posts()

    if not scheduled_posts:
        bot.send_message(chat_id, "No scheduled posts found.")
        return

    # Create inline keyboard with scheduled posts
    inline_keyboard = types.InlineKeyboardMarkup()
    for post in scheduled_posts:
        username, scheduled_time_str, media_id = post
        try:
            channel_info = bot.get_chat(username)
            channel_name = channel_info.title
        except Exception as e:
            logging.error(f"Failed to get information for {username}: {e}")
            channel_name = username  # Fallback to username if fetching channel name fails

        button_text = f"{channel_name} - {scheduled_time_str} - {media_id}"
        inline_keyboard.add(types.InlineKeyboardButton(text=button_text, callback_data=f"view_scheduled_post_{media_id}"))

    # Add "Cancel" button
    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel8"))

    bot.send_message(chat_id, "Scheduled Posts:", reply_markup=inline_keyboard)

def get_scheduled_posts():
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT username, scheduled_time, media_id FROM scheduled_posts')
    rows = cursor.fetchall()
    conn.close()

    current_time = datetime.datetime.now()
    active_posts = []
    for row in rows:
        username, scheduled_time_str, media_id = row
        scheduled_time = datetime.datetime.strptime(scheduled_time_str, "%H %M %d %m")
        scheduled_time = scheduled_time.replace(year=current_time.year)
        if scheduled_time > current_time:
            active_posts.append((username, scheduled_time_str, media_id))

    return active_posts

#FUNGSI DELET SCHEDULE POST
@bot.callback_query_handler(func=lambda call: call.data.startswith("view_scheduled_post_"))
def handle_view_scheduled_post(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    media_id = call.data[len("view_scheduled_post_"):]

    logging.info(f"User {user_id} requested to view scheduled post {media_id}.")

    # Retrieve the scheduled post details from the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT username, scheduled_time FROM scheduled_posts WHERE media_id = ?', (media_id,))
    result = cursor.fetchone()
    if result is None:
        bot.send_message(chat_id, "Scheduled post not found.")
        conn.close()
        return

    username, scheduled_time_str = result

    # Retrieve the media details from the database
    cursor.execute('SELECT media_path, caption, links FROM post_media WHERE id = ?', (media_id,))
    media_result = cursor.fetchone()
    conn.close()

    if media_result is None:
        bot.send_message(chat_id, "Media not found for the scheduled post.")
        return

    media_path, caption, links = media_result

    try:
        channel_info = bot.get_chat(username)
        channel_name = channel_info.title
    except Exception as e:
        logging.error(f"Failed to get information for {username}: {e}")
        channel_name = username  # Fallback to username if fetching channel name fails

    # Create inline keyboard
    inline_keyboard = types.InlineKeyboardMarkup()

    # Parse the links and add them to the inline keyboard
    if links:
        rows = links.split('\n')
        for row in rows:
            buttons = row.split('|')
            for button in buttons:
                try:
                    text, url = button.split('-')
                    inline_keyboard.add(types.InlineKeyboardButton(text=text.strip(), url=url.strip()))
                except ValueError:
                    logging.error(f"Invalid button format: {button}")
                    # Clear the inline keyboard and add only the "Delete Schedule Post" and "Cancel" buttons
                    inline_keyboard = types.InlineKeyboardMarkup()
                    inline_keyboard.add(types.InlineKeyboardButton(text="Delete Schedule Post", callback_data=f"delete_scheduled_post_{media_id}"))
                    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel8"))
                    bot.send_message(chat_id, f"Invalid button format detected: {button}")
                    return

    inline_keyboard.add(types.InlineKeyboardButton(text="Delete Schedule Post", callback_data=f"delete_scheduled_post_{media_id}"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel8"))

    # Check if only caption should be sent
    if not media_path:
        bot.send_message(chat_id, text=caption, reply_markup=inline_keyboard)
    else:
        # Send the media with the caption and inline buttons
        if media_path.endswith('.jpg'):
            bot.send_photo(chat_id, photo=open(media_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
        elif media_path.endswith('.mp4'):
            bot.send_video(chat_id, video=open(media_path, 'rb'), caption=caption, reply_markup=inline_keyboard)
        elif media_path.endswith('.gif'):
            bot.send_document(chat_id, document=open(media_path, 'rb'), caption=caption, reply_markup=inline_keyboard)

    # Send the links as inline buttons
    if links:
        link_keyboard = types.InlineKeyboardMarkup()
        rows = links.split('\n')
        for row in rows:
            buttons = row.split('|')
            for button in buttons:
                try:
                    text, url = button.split('-')
                    link_keyboard.add(types.InlineKeyboardButton(text=text.strip(), url=url.strip()))
                except ValueError:
                    logging.error(f"Invalid button format {button}")
                    bot.send_message(chat_id, f"Invalid button format {button}")
                    return
        

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_scheduled_post_"))
def handle_delete_scheduled_post(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    media_id = call.data[len("delete_scheduled_post_"):]

    logging.info(f"User {user_id} requested to delete scheduled post {media_id}.")

    # Delete the scheduled post from the database
    db_dir = os.path.dirname(__file__)
    db_path = os.path.join(db_dir, 'postmedia.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scheduled_posts WHERE media_id = ?', (media_id,))
    conn.commit()
    conn.close()

    bot.send_message(chat_id, f"Scheduled post {media_id} has been deleted.")
    logging.info(f"Scheduled post {media_id} has been deleted by user {user_id}.")
    channel_post_menu(bot, call)

# Example callback handler for scheduling a post to a single channel
@bot.callback_query_handler(func=lambda call: call.data.startswith("schedule_post_"))
def handle_schedule_post(call):
    chat_id = call.message.chat.id
    username = call.data[len("schedule_post_"):]
    bot.send_message(chat_id, "Please provide the scheduled time in the format: HH MM DD M (e.g., 18 00 12 1)")
    bot.register_next_step_handler_by_chat_id(chat_id, process_scheduled_time, username)

# Example callback handler for scheduling a post to all channels
@bot.callback_query_handler(func=lambda call: call.data == "schedule_post_all")
def handle_schedule_post_all(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Please provide the scheduled time in the format: HH MM DD M (e.g., 18 00 12 1)")
    bot.register_next_step_handler_by_chat_id(chat_id, process_scheduled_time_all)     