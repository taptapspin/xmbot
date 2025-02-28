import os
import json
import logging
import uuid
from config import bot, config, bot_owner_id, bot_admin_ids
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

if 'menus2' not in config:
    config['menus2'] = {}

user_menu_history = {}

# Initialize the config file
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def read_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    else:
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_FILE}")

def write_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

def is_admin_or_owner(user_id):
    return user_id in config['admins'] or user_id == bot_owner_id

def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Special Bonus", callback_data='special_bonus')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)

def button(update, context):
    query = update.callback_query
    query.answer()
    if query.data == 'special_bonus':
        call_send_post2(query.message.chat.id)

def call_send_post2(chat_id):
    send_post2(chat_id)
    
# FINGSI SEND POST/SEND MENU
def send_post2(chat_id):
    media_base_path = os.path.normpath(config['media_path'])
    media_path = config.get('special_promotion_media', os.path.join(media_base_path, 'media_md2.jpg'))
    caption = config.get('special_promotion_caption', "Please choose an option:")
    logging.info(f"Checking if file exists: {media_path}")

    if not os.path.exists(media_path):
        logging.error(f"File does not exist: {media_path}")
        bot.send_message(chat_id, "Media file does not exist. Please upload a new media file.")
        return

    markup = InlineKeyboardMarkup(row_width=2)
    
    button1 = InlineKeyboardButton("JOIN MY🇲🇾", url=config.get('join_my_url', "https://t.me/ecwon8_bot/ec8my"))
    button2 = InlineKeyboardButton("JOIN SG🇸🇬", url=config.get('join_sg_url', "https://t.me/ecwon8_bot/ec8sg"))
    button3 = InlineKeyboardButton("🌟NEW MEMBER PROMOTION🤩", url="https://t.me/ecwon8_bot/ec8bonus")
    markup.add(button3)
    markup.add(button1, button2)
    
    # Add additional promotion buttons from menus2
    if 'menus2' in config:
        for menu_name, menu_data in config['menus2'].items():
            markup.add(InlineKeyboardButton(menu_name, callback_data=f"menu2_{menu_name}"))

    # Add the "Settings Special Bonus" button at the bottom
    if chat_id in config['admins'] or chat_id == bot_owner_id:
        button3 = InlineKeyboardButton("Settings Special Bonus", callback_data="settings_special_bonus")
        markup.add(button3)
    
    # Add the "Back" button at the bottom
    button_back = InlineKeyboardButton("Back", callback_data="back2")
    markup.add(button_back)    

    with open(media_path, 'rb') as media:
        if media_path.endswith(('.jpg', '.jpeg', '.png')):
            bot.send_photo(chat_id, media, caption=caption, reply_markup=markup)
        elif media_path.endswith('.gif'):
            bot.send_animation(chat_id, media, caption=caption, reply_markup=markup)
        elif media_path.endswith('.mp4'):
            bot.send_video(chat_id, media, caption=caption, reply_markup=markup)
        else:
            logging.error("Unsupported media type.")
            bot.send_message(chat_id, "Unsupported media type.")
            return

@bot.callback_query_handler(func=lambda call: call.data == "settings_special_bonus")
def settings_special_bonus_menu(call):
    chat_id = call.message.chat.id
    if not is_admin_or_owner(chat_id):
        bot.send_message(chat_id, "You are not authorized to access this menu.")
        return

    markup = InlineKeyboardMarkup(row_width=2)
    button1 = InlineKeyboardButton("Edit Media Promotion", callback_data="edit2_media_promotion")
    button2 = InlineKeyboardButton("Edit Link Join", callback_data="edit2_link_join")
    button3 = InlineKeyboardButton("Edit Caption Promotion", callback_data="edit2_caption_promotion")
    button4 = InlineKeyboardButton("Add Promotion Button", callback_data="add2_promotion_button")
    button5 = InlineKeyboardButton("Delete Promotion Button", callback_data="delete2_promotion_button")
    button6 = InlineKeyboardButton("Back", callback_data="back2")
    markup.add(button1, button2, button3, button4, button5, button6)

    bot.send_message(chat_id, "Settings Menu Special Bonus:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "edit2_media_promotion")
def edit2_media_promotion(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Please send new media for menu special promotion.")
    bot.register_next_step_handler_by_chat_id(chat_id, receive_new_media)

def receive_new_media(message):
    chat_id = message.chat.id
    if message.content_type not in ['photo', 'video', 'document']:
        bot.send_message(chat_id, "Unsupported media type. Please send a photo, video, or document.")
        return

    file_info = bot.get_file(message.photo[-1].file_id if message.content_type == 'photo' else message.video.file_id if message.content_type == 'video' else message.document.file_id)
    file = bot.download_file(file_info.file_path)

    file_extension = os.path.splitext(file_info.file_path)[1]
    media_base_path = os.path.normpath(config['media_path'])
    media_path = os.path.join(media_base_path, f"media_md2{file_extension}")

    with open(media_path, 'wb') as f:
        f.write(file)

    # Update config with new media path
    config['special_promotion_media'] = media_path
    write_config(config)

    bot.send_message(chat_id, f"Media uploaded successfully and saved as media_md2{file_extension}")

    # Update the special promotion menu with the new media
    send_post2(chat_id)

# FUNGSI EDIT LINK JOIN
@bot.callback_query_handler(func=lambda call: call.data == "edit2_link_join")
def edit2_link_join(call):
    chat_id = call.message.chat.id
    markup = InlineKeyboardMarkup(row_width=2)
    button1 = InlineKeyboardButton("Edit MY🇲🇾 Link", callback_data="edit2_join_my_link")
    button2 = InlineKeyboardButton("Edit SG🇸🇬 Link", callback_data="edit2_join_sg_link")
    button3 = InlineKeyboardButton("Back", callback_data="settings_special_bonus")
    markup.add(button1, button2, button3)
    bot.send_message(chat_id, "Which link would you like to edit?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "edit2_join_my_link")
def edit2_join_my_link(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Please provide the new link for JOIN MY🇲🇾")
    bot.register_next_step_handler_by_chat_id(chat_id, receive_new_join_my_link)

def receive_new_join_my_link(message):
    chat_id = message.chat.id
    new_link = message.text
    config['join_my_url'] = new_link
    write_config(config)
    bot.send_message(chat_id, f"JOIN MY🇲🇾 link updated to: {new_link}")
    send_post2(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "edit2_join_sg_link")
def edit2_join_sg_link(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Please provide the new link for JOIN SG🇸🇬")
    bot.register_next_step_handler_by_chat_id(chat_id, receive_new_join_sg_link)

def receive_new_join_sg_link(message):
    chat_id = message.chat.id
    new_link = message.text
    config['join_sg_url'] = new_link
    write_config(config)
    bot.send_message(chat_id, f"JOIN SG🇸🇬 link updated to: {new_link}")
    send_post2(chat_id)        

# FUNGSI EDIT CAPTION PROMOTION
@bot.callback_query_handler(func=lambda call: call.data == "edit2_caption_promotion")
def edit2_caption_promotion(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Please provide the new caption for the Special Promotion post.")
    bot.register_next_step_handler_by_chat_id(chat_id, receive_new_caption_promotion)

def receive_new_caption_promotion(message):
    chat_id = message.chat.id
    new_caption = message.text
    config['special_promotion_caption'] = new_caption
    write_config(config)
    bot.send_message(chat_id, f"Caption updated to: {new_caption}")
    send_post2(chat_id)

def combined_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Special Promotion"))
    keyboard.add(types.KeyboardButton("Back"))
    return keyboard

MEDIA_FOLDER = os.path.normpath(config['media_path'])

# Load config dengan encoding utf-8
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"Configuration file not found: {CONFIG_FILE}")

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Dictionary untuk menyimpan menu sebelumnya
previous_menu = {}

@bot.callback_query_handler(func=lambda call: call.data == "add2_promotion_button")
def add2_promotion_button(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Please provide the names for the new promotion buttons separated by a comma (e.g., '100% bonus, 200% bonus').")
    bot.register_next_step_handler_by_chat_id(chat_id, receive_new2_button_names)

def receive_new2_button_names(message):
    chat_id = message.chat.id
    button_names = message.text.split(',')
    button_names = [name.strip() for name in button_names]
    
    if len(button_names) == 1:
        position = 'column'
    else:
        position = 'row'
    
    user_menu_history[chat_id] = {'button_names': button_names, 'position': position}
    
    # Initialize the new menus in menus2
    if 'menus2' not in config:
        config['menus2'] = {}
    
    for name in button_names:
        config['menus2'][name] = {
            'caption': '',
            'media_type': '',
            'media_path': '',
            'buttons': [],
            'position': position
        }
    
    write_config(config)
    
    bot.send_message(chat_id, f"New promotion buttons '{', '.join(button_names)}' added successfully.")
    
    # Minta pengguna untuk mengirim media untuk setiap tombol
    request_media(chat_id, button_names)

def request_media(chat_id, button_names):
    bot.send_message(chat_id, "Please send the media (photo or video) for the new promotion buttons.")
    bot.register_next_step_handler_by_chat_id(chat_id, lambda message: receive_media(message, button_names))

def receive_media(message, button_names):
    chat_id = message.chat.id
    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        media_type = 'photo'
    elif message.video:
        file_info = bot.get_file(message.video.file_id)
        media_type = 'video'
    elif message.document:
        file_info = bot.get_file(message.document.file_id)
        media_type = 'document'
    else:
        bot.send_message(chat_id, "No media received. Please send a photo, video, or document.")
        return
    
    downloaded_file = bot.download_file(file_info.file_path)
    
    for name in button_names:
        media_extension = file_info.file_path.split('.')[-1]
        media_path = os.path.join(MEDIA_FOLDER, f"{name}.{media_extension}")
        with open(media_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        config['menus2'][name]['media_type'] = media_type
        config['menus2'][name]['media_path'] = media_path
    
    write_config(config)
    
    bot.send_message(chat_id, "Media has been successfully added to the promotion buttons. Please provide the caption for the promotion buttons.")
    bot.register_next_step_handler_by_chat_id(chat_id, lambda message: receive_caption(message, button_names))

def receive_caption(message, button_names):
    chat_id = message.chat.id
    caption = message.text
    for name in button_names:
        config['menus2'][name]['caption'] = caption
    
    write_config(config)
    
    bot.send_message(chat_id, "Caption has been successfully added to the promotion buttons.")
    send_post2(chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu2_"))
def handle_menu2_button(call):
    chat_id = call.message.chat.id
    menu_name = call.data.split("menu2_")[1]
    
    # Simpan menu sebelumnya
    previous_menu[chat_id] = call.message.message_id
    
    if menu_name in config['menus2']:
        media_type = config['menus2'][menu_name]['media_type']
        media_path = config['menus2'][menu_name]['media_path']
        caption = config['menus2'][menu_name]['caption']
        
        if not os.path.exists(media_path):
            logging.error(f"File does not exist: {media_path}")
            bot.send_message(chat_id, "Media file does not exist. Please upload a new media file.")
            return
        
        markup = create_inline_buttons()
        
        with open(media_path, 'rb') as media:
            if media_type == 'photo':
                bot.send_photo(chat_id, media, caption=caption, reply_markup=markup)
            elif media_type == 'video':
                bot.send_video(chat_id, media, caption=caption, reply_markup=markup)
            elif media_type == 'document':
                bot.send_document(chat_id, media, caption=caption, reply_markup=markup)
            else:
                bot.send_message(chat_id, "Unsupported media type.")
    else:
        bot.send_message(chat_id, "Menu not found.")

@bot.callback_query_handler(func=lambda call: call.data == "back2")
def handle_back2_button(call):
    chat_id = call.message.chat.id
    # Hapus pesan saat ini
    bot.delete_message(chat_id, call.message.message_id)

def create_inline_buttons():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Claim Now 🇲🇾", url="https://t.me/ecwon8_bot/ec8my"),
        InlineKeyboardButton("Claim Now 🇸🇬", url="https://t.me/ecwon8_bot/ec8sg"),
        InlineKeyboardButton("Back", callback_data="back2")
    )
    return markup

def combined_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Special Promotion"))
    keyboard.add(types.KeyboardButton("Back"))
    return keyboard

@bot.message_handler(func=lambda message: message.text == "Special Bonus")
def handle_special_bonus(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Special Bonus Menu", reply_markup=combined_keyboard())

@bot.message_handler(func=lambda message: message.text == "Special Promotion")
def handle_special_promotion(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Here is the Special Promotion!", reply_markup=types.ReplyKeyboardRemove())

# FUNGSI DELET PROMOTION BUTTON
@bot.callback_query_handler(func=lambda call: call.data == "delete2_promotion_button")
def handle_delete2_button(call):
    chat_id = call.message.chat.id
    if 'menus2' not in config or not config['menus2']:
        bot.send_message(chat_id, "No promotion menus available to delete.")
        return

    markup = InlineKeyboardMarkup(row_width=2)
    for menu_name in config['menus2']:
        markup.add(InlineKeyboardButton(menu_name, callback_data=f"delete_menu2_{menu_name}"))
    
    bot.send_message(chat_id, "Select the menu you want to delete:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_menu2_"))
def handle_delete_menu2(call):
    chat_id = call.message.chat.id
    menu2_name = call.data.split("delete_menu2_")[1]
    
    # Remove the menu from the config
    if menu2_name in config['menus2']:
        del config['menus2'][menu2_name]
        write_config(config)
        bot.send_message(chat_id, f"Promotion menu '{menu2_name}' deleted successfully.")
    else:
        bot.send_message(chat_id, f"Promotion menu '{menu2_name}' not found.")
    
    send_post2(chat_id)

#FUNGSI EDIT MEDIA PROMOTION
@bot.message_handler(content_types=['photo', 'video', 'document'])
def handle_media_upload(message):
    if message.chat.id != bot_owner_id and message.chat.id not in bot_admin_ids:
        bot.send_message(message.chat.id, "You are not authorized to upload media.")
        return

    file_info = bot.get_file(message.photo[-1].file_id if message.content_type == 'photo' else message.video.file_id if message.content_type == 'video' else message.document.file_id)
    file = bot.download_file(file_info.file_path)

    file_extension = os.path.splitext(file_info.file_path)[1]
    unique_filename = f"media_md2{file_extension}"
    media_path = os.path.join(config['media_path'], unique_filename)

    with open(media_path, 'wb') as f:
        f.write(file)

    # Update config with new media path
    config['special_promotion_media'] = media_path
    write_config(config)

    bot.send_message(message.chat.id, f"Media uploaded successfully and saved as {unique_filename}")

    # Send the uploaded media back as a preview
    with open(media_path, 'rb') as media:
        if file_extension in ['.jpg', '.jpeg', '.png']:
            bot.send_photo(message.chat.id, media)
        elif file_extension == '.gif':
            bot.send_animation(message.chat.id, media)
        elif file_extension == '.mp4':
            bot.send_video(message.chat.id, media)
        else:
            bot.send_message(message.chat.id, "Unsupported media type for preview.")

def special_promotion_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Special Promotion"))
    return keyboard

