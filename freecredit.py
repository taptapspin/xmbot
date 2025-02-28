import os
import json
import logging
from telebot import types
from configparser import ConfigParser
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import bot, config, bot_owner_id, bot_admin_ids
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

configc = ConfigParser()
configc.read(os.path.join(os.path.dirname(__file__), 'bot_config.txt'))
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

GOOGLE_DRIVE_CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'CREDENTIALS_FILE.json')

user_context = {}

def send_free_credit_post(chat_id):
    gif_url = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMTc3N3I0dnpzOWxtbTlxM2t6MjBmam5qMjZyYWl4ejM3N21tbHVuZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/JpG2A9P3dPHXaTYrwu/giphy.gif"
    
    config = load_config()
    claim_now_my_text = config['button_claim']['claim_now_my']['text']
    claim_now_my_callback = config['button_claim']['claim_now_my']['callback_data']
    claim_now_sg_text = config['button_claim']['claim_now_sg']['text']
    claim_now_sg_callback = config['button_claim']['claim_now_sg']['callback_data']
    caption = config.get('free_credit_caption', "💰Unlock your FREE credit now by following a few simple steps and start winning big! 🎉🔥")
            
    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        types.InlineKeyboardButton(text=claim_now_my_text, callback_data=claim_now_my_callback),
        types.InlineKeyboardButton(text=claim_now_sg_text, callback_data=claim_now_sg_callback)
    )

    # Add Settings Button for owner and admins
    if chat_id in bot_admin_ids or chat_id == bot_owner_id:
        inline_keyboard.add(InlineKeyboardButton(text="⚙️Settings Button⚙️", callback_data="settingclaim_button"))

    inline_keyboard.add(InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_animation(chat_id, gif_url, caption=caption, reply_markup=inline_keyboard)
    logging.info(f"send_free_credit_post called by user_id: {chat_id}")

# Google Sheets ID
SPREADSHEET_ID = configc['DEFAULT']['spreadsheet_id_special_modul']
RANGE_NAMEMY = 'MY REDEEM CODE!A2:F'
RANGE_NAMESG = 'SG REDEEM CODE!A2:F'

def initialize_sheets_api():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_DRIVE_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    sheets_service = build('sheets', 'v4', credentials=creds)
    return sheets_service

def get_next_redeem_code(range_name):
    sheets_service = initialize_sheets_api()
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    values = result.get('values', [])
    
    logging.info(f"Data read from Google Sheets: {values}")  # Log data yang dibaca
    
    for row in values:
        if len(row) >= 1 and (len(row) < 2 or row[1].strip().lower() != 'taken'):
            return row[0], row[1] if len(row) > 1 else '', row[2] if len(row) > 2 else '', row[3] if len(row) > 3 else '', row[4] if len(row) > 4 else '', row[5] if len(row) > 5 else ''
    return None

def mark_redeem_code_as_taken(range_name, redeem_code, phone_number, username, user_id, claim_date_time):
    sheets_service = initialize_sheets_api()
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    values = result.get('values', [])
    for i, row in enumerate(values):
        if row[0] == redeem_code:
            values[i] = [redeem_code, 'Taken', phone_number, username, user_id, claim_date_time]
            break
    body = {
        'values': values
    }
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=range_name,
        valueInputOption='RAW', body=body).execute()

def get_follow_us_button():
    config = load_config()
    button_text = config['button_follow_us']['text']
    button_url = config['button_follow_us']['url']
    return InlineKeyboardButton(text=button_text, url=button_url)

@bot.callback_query_handler(func=lambda call: call.data == "claimmy_now")
def handle_claimmy_now(call):
    chat_id = call.message.chat.id
    user_context[chat_id] = "next_step_my"
    inline_keyboard = InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        get_follow_us_button(),
        InlineKeyboardButton(text="➡️ Next", callback_data="next_step_my")
    )
    if chat_id in bot_admin_ids or chat_id == bot_owner_id:
        inline_keyboard.add(InlineKeyboardButton(text="Settings Button", callback_data="settings_follow_buttons"))
    bot.send_message(chat_id, "Follow a few simple steps below to claim your free bonus credit:\nPlease join our channel and group first to claim your bonus!", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "claimsg_now")
def handle_claimsg_now(call):
    chat_id = call.message.chat.id
    user_context[chat_id] = "next_step_sg"
    inline_keyboard = InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        get_follow_us_button(),
        InlineKeyboardButton(text="➡️ Next", callback_data="next_step_sg")
    )
    if chat_id in bot_admin_ids or chat_id == bot_owner_id:
        inline_keyboard.add(InlineKeyboardButton(text="⚙️Settings Button⚙️", callback_data="settings_follow_buttons"))
    bot.send_message(chat_id, "Follow a few simple steps below to claim your free bonus credit:\nPlease join our channel and group first to claim your bonus!", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "settings_follow_buttons")
def handle_settings_follow_buttons(call):
    chat_id = call.message.chat.id
    inline_keyboard = InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        InlineKeyboardButton(text="Change Button Text", callback_data="change_follow_button_text"),
        InlineKeyboardButton(text="Change Button URL", callback_data="change_follow_button_url"),
        InlineKeyboardButton(text="Back", callback_data="back")
    )
    bot.send_message(chat_id, "Settings for Follow Us button:", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "change_follow_button_text")
def handle_change_follow_button_text(call):
    chat_id = call.message.chat.id
    msg = bot.send_message(chat_id, "Please enter the new button text:")
    bot.register_next_step_handler(msg, update_follow_button_text)

def update_follow_button_text(message):
    new_text = message.text
    config = load_config()
    config['button_follow_us']['text'] = new_text
    save_config(config)
    chat_id = message.chat.id
    bot.send_message(chat_id, f"Button text updated to: {new_text}")
    send_free_credit_post(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "change_follow_button_url")
def handle_change_follow_button_url(call):
    chat_id = call.message.chat.id
    msg = bot.send_message(chat_id, "Please enter the new button URL:")
    bot.register_next_step_handler(msg, update_follow_button_url)

def update_follow_button_url(message):
    new_url = message.text
    config = load_config()
    config['button_follow_us']['url'] = new_url
    save_config(config)
    chat_id = message.chat.id
    bot.send_message(chat_id, f"Button URL updated to: {new_url}")
    send_free_credit_post(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "next_step_my")
def handle_next_step_my(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username

    if is_user_subscribed(user_id):
        if has_user_claimed(user_id, username, RANGE_NAMEMY):
            send_already_claimed_message(chat_id)
        else:
            markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            button = KeyboardButton("Share Contact", request_contact=True)
            markup.add(button)
            bot.send_message(chat_id, "Please share your contact number to proceed.", reply_markup=markup)
    else:
        inline_keyboard = InlineKeyboardMarkup(row_width=1)
        inline_keyboard.add(
            InlineKeyboardButton(text="📲 Follow Us On Telegram", url="https://t.me/addlist/GONwT2LApRMxZDc9"),
            InlineKeyboardButton(text="➡️ Next", callback_data="next_step_my")
        )
        bot.send_message(chat_id, "Follow a few simple steps below to claim your free bonus credit:\nPlease join our channel and group first to claim your bonus!", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "next_step_sg")
def handle_next_step_sg(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username

    if is_user_subscribed(user_id):
        if has_user_claimed(user_id, username, RANGE_NAMESG):
            send_already_claimed_message(chat_id)
        else:
            markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            button = KeyboardButton("Share Contact", request_contact=True)
            markup.add(button)
            bot.send_message(chat_id, "Please share your contact number to proceed.", reply_markup=markup)
    else:
        inline_keyboard = InlineKeyboardMarkup(row_width=1)
        inline_keyboard.add(
            InlineKeyboardButton(text="📲 Follow Us On Telegram", url="https://t.me/addlist/GONwT2LApRMxZDc9"),
            InlineKeyboardButton(text="➡️ Next", callback_data="next_step_sg")
        )
        bot.send_message(chat_id, "Follow a few simple steps below to claim your free bonus credit:\nPlease join our channel and group first to claim your bonus!", reply_markup=inline_keyboard)
        
def is_user_subscribed(user_id):
    channel_username = configc['DEFAULT']['channel_username']
    try:
        member = bot.get_chat_member(channel_username, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Error checking subscription status: {e}")
        return False

def has_user_claimed(user_id, username, range_name):
    sheets_service = initialize_sheets_api()
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    values = result.get('values', [])
    
    for row in values:
        if len(row) >= 4 and (row[3] == username or row[4] == str(user_id)):
            return True
    return False

def get_more_bonus_button():
    config = load_config()
    button_text = config['button_more_bonus']['text']
    button_url = config['button_more_bonus']['url']
    return InlineKeyboardButton(text=button_text, url=button_url)

def send_already_claimed_message(chat_id):
    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        get_more_bonus_button()
    )
    if chat_id in bot_admin_ids or chat_id == bot_owner_id:
        inline_keyboard.add(InlineKeyboardButton(text="⚙️Settings Button⚙️", callback_data="settings_more"))
    inline_keyboard.add(
        InlineKeyboardButton(text="🏘 Main Menu", callback_data="send_post")
    )
    message = (
        "This promotion can only be claimed once per user. 😔\n\n"
        "Unfortunately, you've already received a redeem code for this promotion before, so you won’t be able to claim it again. "
        "But don't worry! You still have the chance to grab other exciting promotions! 🎉\n\n"
        "Visit our promotions page now by clicking the button below and explore what’s waiting for you! 🚀👇"
    )
    bot.send_message(chat_id, message, reply_markup=inline_keyboard)
    bot.send_message(chat_id, "Good luck! Today is the day you hit the jackpot! 🍀💥", reply_markup=types.ReplyKeyboardRemove())

def send_invalid_phone_number_message(chat_id, country):
    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        get_more_bonus_button()
    )
    if chat_id in bot_admin_ids or chat_id == bot_owner_id:
        inline_keyboard.add(InlineKeyboardButton(text="⚙️Settings Button⚙️", callback_data="settings_more"))
    inline_keyboard.add(
        InlineKeyboardButton(text="🏘 Main Menu", callback_data="send_post")
    )
    message = (
        f"Unfortunately, this promotion is only available for {country} user. 😔\n\n"
        "But don’t worry! You still have the chance to explore other exciting promotions! 🎉✨\n\n"
        "🚀 Visit our promotions page now by clicking the button below and discover what’s waiting for you! 👇"
    )
    bot.send_message(chat_id, message, reply_markup=inline_keyboard)
    bot.send_message(chat_id, "Good luck! Today is the day you hit the jackpot! 🍀💥", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if message.contact is not None:
        chat_id = message.chat.id
        user_id = message.from_user.id
        username = message.from_user.username
        phone_number = message.contact.phone_number

        # Log the contact sharing event
        logging.info(f"User {username} (ID: {user_id}) shared contact: {phone_number}")

        # Check if the user has already claimed a redeem code
        if has_user_claimed(user_id, username, RANGE_NAMEMY) or has_user_claimed(user_id, username, RANGE_NAMESG):
            send_already_claimed_message(chat_id)
            return

        # Determine which redeem code to use based on the stored context
        if chat_id in user_context:
            if user_context[chat_id] == "next_step_my":
                if not phone_number.startswith('+60'):
                    send_invalid_phone_number_message(chat_id, "Malaysian")
                    return
                redeem_code_data = get_next_redeem_code(RANGE_NAMEMY)
                mark_function = mark_redeem_code_as_taken
                range_name = RANGE_NAMEMY
            elif user_context[chat_id] == "next_step_sg":
                if not phone_number.startswith('+65'):
                    send_invalid_phone_number_message(chat_id, "Singaporean")
                    return
                redeem_code_data = get_next_redeem_code(RANGE_NAMESG)
                mark_function = mark_redeem_code_as_taken
                range_name = RANGE_NAMESG
            else:
                bot.send_message(chat_id, "❌ Invalid request. Please try again.")
                return
        else:
            bot.send_message(chat_id, "❌ Invalid request. Please try again.")
            return

        if redeem_code_data:
            redeem_code, _, _, _, _, _ = redeem_code_data
            claim_date_time = datetime.now().strftime('%d/%m/%Y %H:%M')

            # Mark the redeem code as taken in Google Sheets
            mark_function(range_name, redeem_code, phone_number, username, user_id, claim_date_time)

            # Create inline keyboard
            inline_keyboard = InlineKeyboardMarkup(row_width=2)
            inline_keyboard.add(
                InlineKeyboardButton(text="Register MY 🇲🇾", url="https://t.me/ecwon8_bot/ec8my"),
            )    
            inline_keyboard.add(
                InlineKeyboardButton(text="Register SG🇸🇬", url="https://t.me/ecwon8_bot/ec8sg")
            )
            inline_keyboard.add(InlineKeyboardButton(text="🏘 Main Menu", callback_data="send_post"))

            # Send the redeem code to the user
            bot.send_message(chat_id, f"🎉 Congratulations! Here is your redeem code:\n{redeem_code}\n\n🚀 Register your account now and redeem this code to get your FREE credit! 💰✨\n\nDon't miss out on this golden opportunity! 🏆🔥", reply_markup=inline_keyboard)
            logging.info(f"Redeem code {redeem_code} sent to user {username} (ID: {user_id})")
        else:
            # Notify the user if no redeem codes are available
            bot.send_message(chat_id, "😔 Sorry, no redeem codes are available at the moment. Please try again tomorrow.")
            logging.info(f"No redeem codes available for user {username} (ID: {user_id})")
    else:
        # Handle the case where contact information is not received
        bot.send_message(chat_id, "❌ Failed to get contact information. Please try again.")
        logging.error(f"Failed to get contact information from user {username} (ID: {user_id})")

    bot.send_message(chat_id, "Good luck! Today is the day you hit the jackpot! 🍀💥", reply_markup=types.ReplyKeyboardRemove())

#------------------------------------PANGGIL MENU UTAMA/SEND_POST DARI SKRIP UTAMA --------------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data == "send_post")
def handle_send_post(call):
    chat_id = call.message.chat.id
    send_post(chat_id)

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
            free_credit = types.InlineKeyboardButton(
                text="🥳Free Credit Bonus💰", 
                callback_data="free_credit"
            )   
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
                text="Lucky Number🍀", 
                callback_data="get_lucky_number"
            )
            inline_keyboard.add(free_credit)
            inline_keyboard.row(join_my_button, join_sg_button)
            inline_keyboard.add(freecr_365_button)
            inline_keyboard.row(lucky_number_button, sport_arena_button)
            
            # Add custom buttons according to their specified format
            row_buttons = []
            if 'custom_buttons' in config:
                for button in config['custom_buttons']:
                    if button['url']:
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
                settings_button = types.InlineKeyboardButton(text="⚙️Settings⚙️", callback_data="settings")
                inline_keyboard.add(settings_button)

            # Check the media type and send accordingly
            media_type = config.get('media_type', 'mp4')
            welcome_message = config.get('welcome_message', 'Welcome!')

            if media_type == 'mp4':
                bot.send_video(chat_id, media, caption=welcome_message, reply_markup=inline_keyboard)
            elif media_type == 'jpg' or media_type == 'png':
                bot.send_photo(chat_id, media, caption=welcome_message, reply_markup=inline_keyboard)
            else:
                bot.send_message(chat_id, "Unsupported media type.")
    except Exception as e:
        logging.error(f"Error sending post: {e}")


#setting button claim
def handle_settingclaim_button(bot, chat_id):
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Change Button Name", callback_data="change_claimbutton_name"),
        types.InlineKeyboardButton(text="Change Button Link", callback_data="change_claimbutton_link"),
        types.InlineKeyboardButton(text="Change Caption", callback_data="change_claim_caption")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Back", callback_data="back")
    )
    bot.send_message(chat_id, "Claim free credit button settings:", reply_markup=inline_keyboard)

def handle_claimchange_button_name(bot, chat_id):
    config = load_config()
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        types.InlineKeyboardButton(text=config['button_claim']['claim_now_my']['text'], callback_data="change_name_claim_now_my"),
        types.InlineKeyboardButton(text=config['button_claim']['claim_now_sg']['text'], callback_data="change_name_claim_now_sg")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Back", callback_data="back")
    )
    bot.send_message(chat_id, "Which button name do you want to change?", reply_markup=inline_keyboard)

def handle_claimchange_button_link(bot, chat_id):
    config = load_config()
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        types.InlineKeyboardButton(text=config['button_claim']['claim_now_my']['text'], callback_data="change_link_claim_now_my"),
        types.InlineKeyboardButton(text=config['button_claim']['claim_now_sg']['text'], callback_data="change_link_claim_now_sg")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Back", callback_data="back")
    )
    bot.send_message(chat_id, "Which button link do you want to change?", reply_markup=inline_keyboard)

def update_claimbutton_name(bot, chat_id, button_key, new_name):
    config = load_config()
    config['button_claim'][button_key]['text'] = new_name
    save_config(config)
    bot.send_message(chat_id, f"Button name updated to: {new_name}")
    send_free_credit_post(chat_id)

def update_claimbutton_link(bot, chat_id, button_key, new_link):
    config = load_config()
    config['button_claim'][button_key]['url'] = new_link
    save_config(config)
    bot.send_message(chat_id, f"Button link updated to: {new_link}")
    send_free_credit_post(chat_id)

def handle_change_claim_caption(bot, chat_id):
    msg = bot.send_message(chat_id, "Please enter the new caption:")
    bot.register_next_step_handler(msg, lambda message: update_claim_caption(bot, chat_id, message.text))

def update_claim_caption(bot, chat_id, new_caption):
    config = load_config()
    config['free_credit_caption'] = new_caption
    save_config(config)
    bot.send_message(chat_id, f"Caption updated to: {new_caption}")
    send_free_credit_post(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "change_claim_caption")
def callback_change_claim_caption(call):
    handle_change_claim_caption(bot, call.message.chat.id)
    
@bot.callback_query_handler(func=lambda call: call.data == "settingclaim_button")
def callback_button_setting(call):
    handle_settingclaim_button(bot, call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "change_claimbutton_name")
def callback_claimchange_button_name(call):
    handle_claimchange_button_name(bot, call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "change_claimbutton_link")
def callback_claimchange_button_link(call):
    handle_claimchange_button_link(bot, call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_name_"))
def callback_update_button_name(call):
    button_key = call.data.replace("change_name_", "")
    msg = bot.send_message(call.message.chat.id, "Please enter the new button name:")
    bot.register_next_step_handler(msg, lambda message: update_claimbutton_name(bot, call.message.chat.id, button_key, message.text))

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_link_"))
def callback_update_button_link(call):
    button_key = call.data.replace("change_link_", "")
    msg = bot.send_message(call.message.chat.id, "Please enter the new button link:")
    bot.register_next_step_handler(msg, lambda message: update_claimbutton_link(bot, call.message.chat.id, button_key, message.text))    

def handle_settings_more_button(bot, chat_id):
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Change Button Name", callback_data="change_more_button_name"),
        types.InlineKeyboardButton(text="Change Button Link", callback_data="change_more_button_link"),
        types.InlineKeyboardButton(text="Back", callback_data="back")
    )
    bot.send_message(chat_id, "More Bonus button settings:", reply_markup=inline_keyboard)

#fungsi setting more
def update_more_button_name(bot, chat_id, new_name):
    config = load_config()
    config['button_more_bonus']['text'] = new_name
    save_config(config)
    bot.send_message(chat_id, f"Button name updated to: {new_name}")
    send_free_credit_post(chat_id)

def update_more_button_link(bot, chat_id, new_link):
    config = load_config()
    config['button_more_bonus']['url'] = new_link
    save_config(config)
    bot.send_message(chat_id, f"Button link updated to: {new_link}")
    send_free_credit_post(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "settings_more")
def callback_settings_more_button(call):
    handle_settings_more_button(bot, call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "change_more_button_name")
def callback_change_more_button_name(call):
    msg = bot.send_message(call.message.chat.id, "Please enter the new button name:")
    bot.register_next_step_handler(msg, lambda message: update_more_button_name(bot, call.message.chat.id, message.text))

@bot.callback_query_handler(func=lambda call: call.data == "change_more_button_link")
def callback_change_more_button_link(call):
    msg = bot.send_message(call.message.chat.id, "Please enter the new button link:")
    bot.register_next_step_handler(msg, lambda message: update_more_button_link(bot, call.message.chat.id, message.text))
         