import telebot
from telebot import types
import os
import time
import json
import logging
import openpyxl
from datetime import datetime
from xbot2 import add_link_button_menu, delete_link_button_menu, handle_delete_link_button, handle_add_link_button_direct, delete_menu_menu, handle_delete_menu, handle_edit_button_name
from xbot3 import handle_add_menu
from xbot4 import send_post2, special_promotion_keyboard
from broadcast import send_broadcast_menu, handle_broadcast_menu
from config import bot, config, back_keyboard, bot_owner_id
from telebot import apihelper
from channel import channel_post_menu, handle_add_post_media_channel, reload_scheduled_posts
from freecredit import send_free_credit_post
from lottery import send_random_lottery_gif
from sport import send_sport_arena_post
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Setup logging
logging.basicConfig(level=logging.INFO)

def run_bot():
    while True:
        try:
            reload_scheduled_posts()
            bot.polling(none_stop=True, interval=0, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Bot terminated with error: {e}")
            print("Restarting bot in 5 seconds...")
            time.sleep(5)

# Define the base directory from environment variable or default to current directory
base_dir = os.getenv('BASE_DIR', os.path.dirname(__file__))

# Define file paths using environment variable
user_chat_ids_file = os.path.join(base_dir, 'user_chat_ids.json')
user_data_file = os.path.join(base_dir, 'user_data.xlsx')
config_file = os.path.join(base_dir, 'config.json')
broadcasts_db_file = os.path.join(base_dir, 'broadcasts.db')
postmedia_db_file = os.path.join(base_dir, 'postmedia.db')
bot_config_file = os.path.join(base_dir, 'bot_config.txt')

def read_config():
    if not os.path.exists(config_file):
        return {}
    with open(config_file, 'r') as file:
        return json.load(file)

def write_config(config):
    with open(config_file, 'w') as file:
        json.dump(config, file, indent=4)    

def reload_config():
    global config
    config = read_config()
    logging.info("Configuration reloaded")

# Initialize 'menus' key in config if not present
if 'menus' not in config:
    config['menus'] = {}

# Dictionary to store user menu history
user_menu_history = {}

apihelper.CONNECT_TIMEOUT = 30
apihelper.READ_TIMEOUT = 30

#FUNGSI CALL LUCKY NUMBERS
@bot.callback_query_handler(func=lambda call: call.data == "get_lucky_number")
def handle_get_lucky_number(call):
    logging.info(f"Handling get_lucky_number callback for chat_id: {call.message.chat.id}")
    bot.answer_callback_query(call.id)
    send_random_lottery_gif(bot, call.message.chat.id)

#FUNGSI CALL SPORT ARENA
@bot.callback_query_handler(func=lambda call: call.data == "sport_arena")
def handle_sport_arena(call):
    send_sport_arena_post(call.message.chat.id)

#FUNGSI FREE CREDIT
@bot.callback_query_handler(func=lambda call: call.data == "free_credit")
def handle_free_credit(call):
    logging.info(f"Handling free_credit callback for chat_id: {call.message.chat.id}")
    bot.answer_callback_query(call.id)
    send_free_credit_post(call.message.chat.id)

@bot.message_handler(commands=['start'])
def bot_start(message):
    logging.info(f"Received /start command from {message.chat.id}")
    reload_config()
    user_menu_history[message.chat.id] = []
    handle_new_user(message)
    send_post(message.chat.id)


# Define the list_admins_command function
def list_admins_command(message):
    logging.info(f"User ID: {message.from_user.id}, Bot Owner ID: {bot_owner_id}, Admins: {config['admins']}")
    admin_list = "\n".join([f"{bot.get_chat(admin).username} (ID: {admin})" for admin in config['admins']])

    # Create inline keyboard with "Back" button
    keyboard = types.InlineKeyboardMarkup()
    back_button = types.InlineKeyboardButton(text="Back", callback_data="back")
    keyboard.add(back_button)

    bot.send_message(message.chat.id, f"Current admins:\n{admin_list}", reply_markup=keyboard)

# Handle the callback query for "list_admins"
@bot.callback_query_handler(func=lambda call: call.data == "list_admins")
def callback_query_handler(call):
    list_admins_command(call.message)

# Handle the callback query for "back"
@bot.callback_query_handler(func=lambda call: call.data == "back")
def callback_query_handler_back(call):
    send_main_menu(call.message.chat.id)

# Define the button for listing admins
list_admins_button = types.InlineKeyboardButton(text="List Admins", callback_data="list_admins")

def send_main_menu(chat_id):
    main_menu_keyboard = types.InlineKeyboardMarkup()
    for menu_name in config['menus']:
        main_menu_keyboard.add(types.InlineKeyboardButton(text=menu_name, callback_data=f"menu_{menu_name}"))
    bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu_keyboard)

def send_post(chat_id):
    logging.info(f"Sending post to {chat_id}")

    # Get the media path from the configuration
    media_base_path = os.path.normpath(config['media_path'])
    media_type = config.get('media_type', 'mp4')  # Default to 'mp4' if not set
    media_path = os.path.join(media_base_path, f'media_{config["media_number"]}.{media_type}')

    logging.info(f"Media path: {media_path}")
    try:
        with open(media_path, 'rb') as media:
            inline_keyboard = types.InlineKeyboardMarkup() 
        
            # Conditionally add the Free Credit Bonus button
            if config.get('free_credit_button_visible', True):
                free_credit = types.InlineKeyboardButton(
                    text="🥳Free Credit Bonus💰", 
                    callback_data="free_credit"
                )
                inline_keyboard.add(free_credit)
        
            join_my_button = types.InlineKeyboardButton(
                text=config.get('join_my_text', "JOIN MY🇲🇾"), 
                url=config.get('join_my_url', 'https://example.com')
            )
            join_sg_button = types.InlineKeyboardButton(
                text=config.get('join_sg_text', "JOIN SG🇸🇬"), 
                url=config.get('join_sg_url', 'https://example.com')
            )
            freecr_365_button = types.InlineKeyboardButton(
                text=config.get('freecr_365_text', "🤑 FREE CREDIT 🤑"), 
                url=config.get('freecr_365_url', 'https://example.com')
            )
            sport_arena_button = types.InlineKeyboardButton(
                text="⚽️ Football Schedule", 
                callback_data="sport_arena"
            )   
            lucky_number_button = types.InlineKeyboardButton(
                text="🍀Lucky Number", 
                callback_data="get_lucky_number"
            )
            inline_keyboard.row(join_my_button, join_sg_button)
            inline_keyboard.add(freecr_365_button)
            inline_keyboard.row(lucky_number_button, sport_arena_button)
        
            # Add custom buttons according to their specified format
            row_buttons = []
            if 'custom_buttons' in config:
                for button in config['custom_buttons']:
                    if button['url']:  # Only add buttons with a URL
                        if button['type'] == 'row':
                            row_buttons.append(types.InlineKeyboardButton(text=button['text'], url=button['url']))
                        else:
                            inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], url=button['url']))
        
            # Add row buttons in a single row
            if row_buttons:
                inline_keyboard.row(*row_buttons)

            # Add menu buttons
            if 'menus' in config:
                for menu_name in config['menus']:
                    inline_keyboard.add(types.InlineKeyboardButton(text=menu_name, callback_data=f"menu_{menu_name}"))
        
            if chat_id in config['admins'] or chat_id == bot_owner_id:
                broadcast_button = types.InlineKeyboardButton(text="📢 Broadcast 📢", callback_data="broadcast")
                inline_keyboard.add(broadcast_button)
                channel_post = types.InlineKeyboardButton(text="📥 Channel Post 📥", callback_data="channelpost")
                inline_keyboard.add(channel_post)
            
                # Add the toggle button for Free Credit Bonus
                free_credit_toggle_text = "Free Credit On" if config.get('free_credit_button_visible', True) else "Free Credit Off"
                free_credit_toggle_button = types.InlineKeyboardButton(text=free_credit_toggle_text, callback_data="toggle_free_credit")
                inline_keyboard.add(free_credit_toggle_button)
            
                settings_button = types.InlineKeyboardButton(text="⚙️Settings⚙️", callback_data="settings")
                inline_keyboard.add(settings_button)
        
            # Check the media type and send accordingly
            media_type = config.get('media_type', 'mp4')
            welcome_message = config.get('welcome_message', 'Welcome!')
            if media_type in ['jpg', 'jpeg', 'png']:
                bot.send_photo(chat_id, media, caption=welcome_message, reply_markup=inline_keyboard)
            elif media_type == 'gif':
                bot.send_animation(chat_id, media, caption=welcome_message, reply_markup=inline_keyboard)
            elif media_type == 'mp4':
                bot.send_video(chat_id, media, caption=welcome_message, reply_markup=inline_keyboard)
            else:
                logging.error("Unsupported media type.")
                bot.send_message(chat_id, "Unsupported media type.")
    except FileNotFoundError:
        logging.error(f"File not found: {media_path}")
        bot.send_message(chat_id, 'Sorry, the media file is not available.', reply_markup=back_keyboard())
        send_main_menu(chat_id)  # Panggil fungsi send_main_menu jika file media tidak tersedia

@bot.callback_query_handler(func=lambda call: call.data == "toggle_free_credit")
def handle_toggle_free_credit(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    config['free_credit_button_visible'] = not config.get('free_credit_button_visible', True)
    write_config(config)

    # Refresh the settings menu
    send_post(chat_id)

# Add this function to handle the broadcast button press
@bot.callback_query_handler(func=lambda call: call.data == "channelpost")
def handle_channel_post_button(call):
    bot.answer_callback_query(call.id)
    channel_post_menu(bot, call)

@bot.callback_query_handler(func=lambda call: call.data == "add_post8_media")
def handle_add_post_media_callback(call):
    bot.answer_callback_query(call.id)
    handle_add_post_media_channel(bot, call)

# Add this function to handle the broadcast button press
@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def handle_broadcast_button(call):
    bot.answer_callback_query(call.id)
    if call.data == 'broadcast':
        call_send_broadcast_menu(call.message.chat.id)

def call_send_broadcast_menu(chat_id):
    send_broadcast_menu(chat_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    logging.info(f"Received callback query with data: {call.data} from {call.message.chat.id}")
    if call.from_user.id in config['admins'] or call.from_user.id == bot_owner_id:
        if call.data == "settings":
            add_to_history(call.message.chat.id, settings_submenu)
            settings_submenu(call.message)
        elif call.data == "edit_caption":
            msg = bot.send_message(call.message.chat.id, "Please send the new welcome message.", reply_markup=back_keyboard())
            bot.register_next_step_handler(msg, set_welcome)
        elif call.data == "edit_media":
            msg = bot.send_message(call.message.chat.id, "Please send the new video or image file.", reply_markup=back_keyboard())
            bot.register_next_step_handler(msg, set_welcome_media)
        elif call.data == "edit_links":
            add_to_history(call.message.chat.id, edit_links_submenu)
            edit_links_submenu(call.message)
        elif call.data == "edit_button_name":
            handle_edit_button_name(call)
        elif call.data == "edit_join_my":
            msg = bot.send_message(call.message.chat.id, "Please send the new JOIN MY link.", reply_markup=back_keyboard())
            bot.register_next_step_handler(msg, set_join_my)
        elif call.data == "edit_join_sg":
            msg = bot.send_message(call.message.chat.id, "Please send the new JOIN SG link.", reply_markup=back_keyboard())
            bot.register_next_step_handler(msg, set_join_sg)
        elif call.data == "edit_freecr_365":
            msg = bot.send_message(call.message.chat.id, "Please send the new FREE CREDIT link.", reply_markup=back_keyboard())
            bot.register_next_step_handler(msg, set_freecr_365)
        elif call.data == "add_admin":
            msg = bot.send_message(call.message.chat.id, "Please send the Telegram user ID of the new admin.", reply_markup=back_keyboard())
            bot.register_next_step_handler(msg, add_admin)
        elif call.data == "remove_admin":
            msg = bot.send_message(call.message.chat.id, "Please send the Telegram user ID of the admin to remove.", reply_markup=back_keyboard())
            bot.register_next_step_handler(msg, remove_admin)
        elif call.data == "add_link_button":
            handle_add_link_button_direct(call)
        elif call.data == "add_menu":
            handle_add_menu(call)
        elif call.data == "preview_post":
            preview_post(call.message)
        elif call.data == "delete_link_button":
            delete_link_button_menu(call.message)
        elif call.data.startswith("delete_link_"):
            button_text = call.data[len("delete_link_"):]
            handle_delete_link_button(call)
        elif call.data == "delete_menu":
            delete_menu_menu(call.message)
        elif call.data.startswith("delete_menu_"):
            menu_name = call.data[len("delete_menu_"):]
            handle_delete_menu(call)
        elif call.data == "post_sub_menu":
            msg = bot.send_message(call.message.chat.id, "Please send the new post media (photo or video).", reply_markup=back_keyboard())
            bot.register_next_step_handler(msg, lambda m: set_new_post_media(bot, m, config, write_config, back_keyboard))
        elif call.data.startswith("menu_"):
            menu_name = call.data[len("menu_"):]
            show_menu_content(call.message, menu_name)
        else:
            bot.answer_callback_query(call.id, "You are not authorized to perform this action.")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def handle_cancel_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

def show_menu_content(message, menu_name):
    if menu_name in config['menus']:
        menu = config['menus'][menu_name]
        media_path = menu['media_path']
        caption = menu['caption']
        try:
            with open(media_path, 'rb') as media:
                inline_keyboard = types.InlineKeyboardMarkup()
                if message.from_user.id in config['admins']:
                    settings_button = types.InlineKeyboardButton(text="Settings", callback_data="settings")
                    inline_keyboard.add(settings_button)
                if menu['media_type'] == 'video':
                    bot.send_video(message.chat.id, media, caption=caption, reply_markup=inline_keyboard)
                else:
                    bot.send_photo(message.chat.id, media, caption=caption, reply_markup=inline_keyboard)
        except FileNotFoundError:
            bot.send_message(message.chat.id, 'Sorry, the media file is not available.', reply_markup=back_keyboard())
    else:
        bot.send_message(message.chat.id, f'Menu "{menu_name}" not found.', reply_markup=back_keyboard())

@bot.message_handler(func=lambda message: message.text == "Back")
def handle_back(message):
    send_previous_menu(message)

def add_to_history(chat_id, menu_function):
    if chat_id not in user_menu_history:
        user_menu_history[chat_id] = []
    user_menu_history[chat_id].append(menu_function)

def send_previous_menu(message):
    chat_id = message.chat.id
    if chat_id in user_menu_history and user_menu_history[chat_id]:
        previous_menu = user_menu_history[chat_id].pop()
        if previous_menu in [settings_submenu, edit_links_submenu, link_button_menu]:
            previous_menu(message)
        else:
            previous_menu(bot, message, config, back_keyboard)
    else:
        bot.send_message(chat_id, "Returning to main menu.", reply_markup=types.ReplyKeyboardRemove())
        bot_start(message)

def settings_submenu(message):
    settings_keyboard = types.InlineKeyboardMarkup()
    edit_caption_button = types.InlineKeyboardButton(text="Edit Caption", callback_data="edit_caption")
    edit_media_button = types.InlineKeyboardButton(text="Edit Media", callback_data="edit_media")
    edit_links_button = types.InlineKeyboardButton(text="Edit Links", callback_data="edit_links")
    edit_button_name_button = types.InlineKeyboardButton(text="Edit Button Name", callback_data="edit_button_name")
    add_link_button = types.InlineKeyboardButton(text="Add Link Button", callback_data="add_link_button")
    add_menu_button = types.InlineKeyboardButton(text="Add Menu", callback_data="add_menu")
    delete_link_button = types.InlineKeyboardButton(text="Delete Link Button", callback_data="delete_link_button")
    delete_menu_button = types.InlineKeyboardButton(text="Delete Menu", callback_data="delete_menu")
    list_admins_button = types.InlineKeyboardButton(text="List Admins", callback_data="list_admins")
    add_admin_button = types.InlineKeyboardButton(text="Add Admin", callback_data="add_admin")
    remove_admin_button = types.InlineKeyboardButton(text="Remove Admin", callback_data="remove_admin")
    cancel_button = types.InlineKeyboardButton(text="Cancel", callback_data="cancel")
    

    settings_keyboard.row(edit_caption_button, edit_media_button)
    settings_keyboard.add(edit_links_button)
    settings_keyboard.add(edit_button_name_button)
    settings_keyboard.row(add_link_button, add_menu_button)
    settings_keyboard.row(delete_link_button, delete_menu_button)
    settings_keyboard.add(list_admins_button)
    settings_keyboard.row(add_admin_button, remove_admin_button)
    settings_keyboard.add(cancel_button)
    
    bot.send_message(message.chat.id, "Settings Menu:", reply_markup=settings_keyboard)
    

def edit_links_submenu(message):
    links_keyboard = types.InlineKeyboardMarkup()
    edit_join_my_button = types.InlineKeyboardButton(text=f"Edit {config.get('join_my_text', 'JOIN MY🇲🇾')} Link", callback_data="edit_join_my")
    edit_join_sg_button = types.InlineKeyboardButton(text=f"Edit {config.get('join_sg_text', 'JOIN SG🇸🇬')} Link", callback_data="edit_join_sg")
    edit_freecr_365_button = types.InlineKeyboardButton(text=f"Edit {config.get('freecr_365_text', '🤑 FREE CREDIT 🤑')} Link", callback_data="edit_freecr_365")
    cancel_button = types.InlineKeyboardButton(text="Cancel", callback_data="cancel")
    
    links_keyboard.add(edit_join_my_button)
    links_keyboard.add(edit_join_sg_button)
    links_keyboard.add(edit_freecr_365_button)
    links_keyboard.add(cancel_button)
    
    bot.send_message(message.chat.id, "Edit Links Menu:", reply_markup=links_keyboard)
    

def link_button_menu(message):
    link_button_keyboard = types.InlineKeyboardMarkup()
    add_link_button = types.InlineKeyboardButton(text="Add Link Button", callback_data="add_link_button")
    add_menu_button = types.InlineKeyboardButton(text="Add Menu", callback_data="add_menu")
    preview_post_button = types.InlineKeyboardButton(text="Preview Post", callback_data="preview_post")
    cancel_button = types.InlineKeyboardButton(text="Cancel", callback_data="cancel")
    
    link_button_keyboard.row(add_link_button, add_menu_button)
    link_button_keyboard.add(preview_post_button)
    link_button_keyboard.add(cancel_button)
    
    bot.send_message(message.chat.id, "Link Button Menu:", reply_markup=link_button_keyboard)
    

def preview_post(message):
    send_post(message.chat.id)

def set_welcome(message):
    if message.from_user.id in config['admins'] or message.from_user.id == bot_owner_id:
        config['welcome_message'] = message.text
        write_config(config)
        bot.reply_to(message, 'Welcome message updated successfully.', reply_markup=back_keyboard())
    else:
        bot.reply_to(message, 'You are not authorized to perform this action.', reply_markup=back_keyboard())

def set_welcome_media(message):
    if message.from_user.id in config['admins'] or message.from_user.id == bot_owner_id:
        media_base_path = os.path.normpath(config['media_path'])
        
        # Hapus media lama jika ada
        old_media_path = os.path.join(media_base_path, f'media_{config["media_number"]}.{config["media_type"]}')
        if os.path.exists(old_media_path):
            os.remove(old_media_path)
        
        if message.content_type == 'photo':
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            media_path = os.path.join(media_base_path, f'media_{config["media_number"]}.jpg')
            with open(media_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            config['media_type'] = 'jpg'
        elif message.content_type == 'video':
            file_info = bot.get_file(message.video.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            media_path = os.path.join(media_base_path, f'media_{config["media_number"]}.mp4')
            with open(media_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            config['media_type'] = 'mp4'
        else:
            bot.reply_to(message, 'Invalid media type. Please send a photo or video.', reply_markup=back_keyboard())
            return
        
        # Update config with new media path and type
        config['welcome_media_path'] = media_path
        write_config(config)
        
        bot.reply_to(message, 'Welcome media updated successfully.', reply_markup=back_keyboard())
    else:
        bot.reply_to(message, 'You are not authorized to perform this action.', reply_markup=back_keyboard())

def add_admin(message):
    if message.from_user.id in config['admins'] or message.from_user.id == bot_owner_id:
        try:
            new_admin_id = int(message.text)
            if new_admin_id == bot.id:
                bot.reply_to(message, 'Invalid ID. You cannot add the bot as an admin.', reply_markup=back_keyboard())
                return
            if new_admin_id not in config['admins']:
                config['admins'].append(new_admin_id)
                write_config(config)
                bot.reply_to(message, 'Admin added successfully.', reply_markup=back_keyboard())
                logging.info(f"Admin added: {new_admin_id}")
            else:
                bot.reply_to(message, 'This user is already an admin.', reply_markup=back_keyboard())
        except ValueError:
            bot.reply_to(message, 'Invalid format. Please send a valid Telegram user ID.', reply_markup=back_keyboard())
            logging.error("Invalid format for admin ID.")
    else:
        bot.reply_to(message, 'You are not authorized to perform this action.', reply_markup=back_keyboard())
        logging.warning(f"Unauthorized admin addition attempt by user: {message.from_user.id}")

def remove_admin(message):
    if message.from_user.id in config['admins'] or message.from_user.id == bot_owner_id:
        try:
            admin_id = int(message.text)
            if admin_id in config['admins']:
                config['admins'].remove(admin_id)
                write_config(config)
                bot.reply_to(message, 'Admin removed successfully.', reply_markup=back_keyboard())
                logging.info(f"Admin removed: {admin_id}")
            else:
                bot.reply_to(message, 'This user is not an admin.', reply_markup=back_keyboard())
        except ValueError:
            bot.reply_to(message, 'Invalid format. Please send a valid Telegram user ID.', reply_markup=back_keyboard())
            logging.error("Invalid format for admin ID.")
    else:
        bot.reply_to(message, 'You are not authorized to perform this action.', reply_markup=back_keyboard())
        logging.warning(f"Unauthorized admin removal attempt by user: {message.from_user.id}")

# new script additions
# Load user chat IDs
def load_user_chat_ids():
    try:
        with open(user_chat_ids_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Save user chat IDs
def save_user_chat_ids(chat_ids):
    with open(user_chat_ids_file, 'w') as file:
        json.dump(chat_ids, file)

# Path to your Google Drive API credentials JSON file
GOOGLE_DRIVE_CREDENTIALS_FILE = os.path.join(script_dir, '..', 'utils', 'setup', 'CREDENTIALS_FILE.json')

# Google Sheets ID
SPREADSHEET_ID = '1x9B-XxkJPsbkKguw6zAOFO8YPEDzqRooLJA_OefKsVU'  # Replace with your Google Sheets ID
RANGE_NAME = 'MAIN BOT!A1:D1'  # Adjust the range as needed

# Save user data to Excel
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

# Tambahkan logika penyimpanan data pengguna baru
def handle_new_user(message):
    user_id = message.from_user.id
    username = message.from_user.username
    phone_number = message.contact.phone_number if message.contact else 'N/A'

    logging.info(f"Handling new user: {user_id}, {username}, {phone_number}")

    chat_ids = load_user_chat_ids()
    if user_id not in chat_ids:
        chat_ids.append(user_id)
        save_user_chat_ids(chat_ids)
        save_user_data_to_sheets(user_id, username, phone_number)
        logging.info(f"New user added: {user_id}")

def send_settings_menu(chat_id):
    settings_menu_keyboard = types.InlineKeyboardMarkup()
    add_menu_button = types.InlineKeyboardButton(text="Add Menu", callback_data="add_menu")
    settings_menu_keyboard.add(add_menu_button)
    bot.send_message(chat_id, "Settings Menu:", reply_markup=settings_menu_keyboard)

@bot.message_handler(func=lambda message: message.text == "Start Over")
def handle_start_over(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    logging.info(f"User {user_id} pressed 'Start Over' button.")
    bot_start(message)

#PINDAHAN TERAKHIR
def set_join_my(message):
    if message.from_user.id in config['admins'] or message.from_user.id == bot_owner_id:
        config['join_my_url'] = message.text
        write_config(config)
        bot.reply_to(message, f'{config.get("join_my_text", "JOIN MY🇲🇾")} link updated successfully.', reply_markup=back_keyboard())
    else:
        bot.reply_to(message, 'You are not authorized to perform this action.', reply_markup=back_keyboard())

def set_join_sg(message):
    if message.from_user.id in config['admins'] or message.from_user.id == bot_owner_id:
        config['join_sg_url'] = message.text
        write_config(config)
        bot.reply_to(message, f'{config.get("join_sg_text", "JOIN SG🇸🇬")} link updated successfully.', reply_markup=back_keyboard())
    else:
        bot.reply_to(message, 'You are not authorized to perform this action.', reply_markup=back_keyboard())

def set_freecr_365(message):
    if message.from_user.id in config['admins'] or message.from_user.id == bot_owner_id:
        config['freecr_365_url'] = message.text
        write_config(config)
        bot.reply_to(message, f'{config.get("freecr_365_text", "🤑 FREE CREDIT 🤑")} link updated successfully.', reply_markup=back_keyboard())
    else:
        bot.reply_to(message, 'You are not authorized to perform this action.', reply_markup=back_keyboard())
        
def set_new_post_media(bot, message, config, save_config, back_keyboard):
    if message.content_type in ['photo', 'video']:
        file_info = bot.get_file(message.photo[-1].file_id if message.content_type == 'photo' else message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        media_path = os.path.join('C:/Users/fortu/OneDrive/Documents/888 file/BOT Project/Media/', f'{config["media_number"]}_media')
        with open(media_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        config['media_type'] = message.content_type
        config['media_path'] = media_path
        write_config(config)
        bot.reply_to(message, 'New post media updated successfully.', reply_markup=back_keyboard())
    else:
        bot.reply_to(message, 'Invalid media type. Please send a photo or video.', reply_markup=back_keyboard())

# Pastikan fungsi remove_link_button didefinisikan di sini
def remove_link_button(message, button_text):
    if message.from_user.id in config['admins'] or message.from_user.id == bot_owner_id:
        for button in config['custom_buttons']:
            if button['text'] == button_text:
                config['custom_buttons'].remove(button)
                write_config(config)
                bot.reply_to(message, f'Link button "{button_text}" removed successfully.', reply_markup=back_keyboard())
                return
        bot.reply_to(message, 'Button not found.', reply_markup=back_keyboard())
    else:
        bot.reply_to(message, 'You are not authorized to perform this action.', reply_markup=back_keyboard())


if __name__ == "__main__":
    print("Starting bot...")
    run_bot()
