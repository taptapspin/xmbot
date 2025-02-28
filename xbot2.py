import telebot
from telebot import types
import os
import json
from config import bot, config, back_keyboard, bot_owner_id
import logging

logging.basicConfig(level=logging.INFO)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def write_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    logging.info(f"Configuration saved to {CONFIG_FILE}")

def read_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        logging.error(f"Configuration file not found: {CONFIG_FILE}")
        return {}

def reload_config():
    global config
    config = read_config()
    logging.info("Configuration reloaded")

# Load the configuration at the start
config = read_config()

def add_link_button_menu(message):
    logging.info(f"User {message.from_user.username} (ID: {message.from_user.id}) opened the add link button menu.")
    keyboard = types.InlineKeyboardMarkup()
    add_link_button = types.InlineKeyboardButton(text="Add Link Button", callback_data="add_link_button_direct")
    add_menu_button = types.InlineKeyboardButton(text="Add Menu", callback_data="add_menu")
    preview_post_button = types.InlineKeyboardButton(text="Preview Post", callback_data="preview_post")
    cancel_button = types.InlineKeyboardButton(text="Cancel", callback_data="cancel")
    
    keyboard.add(add_link_button)
    keyboard.add(add_menu_button)
    keyboard.add(preview_post_button)
    keyboard.add(cancel_button)
    
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "add_link_button_direct")
def handle_add_link_button_direct(call):
    logging.info(f"User {call.from_user.username} (ID: {call.from_user.id}) selected to add a link button directly.")
    msg = bot.send_message(call.message.chat.id, "Please send the button text and URL in the format: text - url. For multiple buttons in a row, separate them with ' | '. For vertical buttons, use new lines.", reply_markup=back_keyboard())
    bot.register_next_step_handler(msg, add_link_button)

def add_link_button(message):
    try:
        rows = message.text.split('\n')
        for row in rows:
            buttons = row.split(' | ')
            for btn in buttons:
                text, url = btn.split(' - ')
                config['custom_buttons'].append({'text': text.strip(), 'url': url.strip(), 'type': 'row' if ' | ' in row else 'add'})
        write_config(config)
        reload_config()  # Reload configuration after writing
        logging.info(f"User {message.from_user.username} (ID: {message.from_user.id}) added link button(s): {message.text}")
        bot.reply_to(message, 'Link button(s) added successfully.', reply_markup=back_keyboard())
    except ValueError:
        logging.error(f"User {message.from_user.username} (ID: {message.from_user.id}) provided invalid format for link button(s): {message.text}")
        bot.reply_to(message, 'Invalid format. Please use the format: text - url. For multiple buttons in a row, separate them with " | ". For vertical buttons, use new lines.', reply_markup=back_keyboard())

def delete_link_button_menu(message):
    logging.info(f"User {message.from_user.username} (ID: {message.from_user.id}) opened the delete link button menu.")
    inline_keyboard = types.InlineKeyboardMarkup()
    
    # Add custom buttons to the inline keyboard
    for button in config['custom_buttons']:
        inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], callback_data=f"delete_link_{button['text']}"))
    
    # Add default buttons to the inline keyboard
    default_buttons = [
        {"text": config.get('join_my_text', "JOIN MY🇲🇾"), "url": config['join_my_url']},
        {"text": config.get('join_sg_text', "JOIN SG🇸🇬"), "url": config['join_sg_url']},
        {"text": config.get('freecr_365_text', "🤑 FREE CREDIT 🤑"), "url": config['freecr_365_url']}
    ]
    for button in default_buttons:
        inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], callback_data=f"delete_link_{button['text']}"))
    
    # Add a cancel button
    cancel_button = types.InlineKeyboardButton(text="Cancel", callback_data="cancel")
    inline_keyboard.add(cancel_button)
    
    bot.send_message(message.chat.id, "Select a button to delete:", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_link_"))
def handle_delete_link_button(call):
    button_text = call.data[len("delete_link_"):]
    logging.info(f"User {call.from_user.username} (ID: {call.from_user.id}) selected to delete link button: {button_text}")
    
    # Remove the button from custom_buttons if it exists
    config['custom_buttons'] = [button for button in config['custom_buttons'] if button['text'] != button_text]
    write_config(config)
    reload_config()  # Reload configuration after writing
    bot.answer_callback_query(call.id, "Button deleted successfully.")
    bot.send_message(call.message.chat.id, "Button deleted successfully.", reply_markup=back_keyboard())
    
    # Remove the button from default_buttons if it exists
    default_buttons = [
        {"text": config.get('join_my_text', "JOIN MY🇲🇾"), "url": config['join_my_url']},
        {"text": config.get('join_sg_text', "JOIN SG🇸🇬"), "url": config['join_sg_url']},
        {"text": config.get('freecr_365_text', "🤑 FREE CREDIT 🤑"), "url": config['freecr_365_url']}
    ]
    default_buttons = [button for button in default_buttons if button['text'] != button_text]
    
    write_config(config)
    reload_config()  # Reload configuration after writing
    
    # Refresh the inline keyboard with the remaining buttons
    inline_keyboard = types.InlineKeyboardMarkup()
    for button in config['custom_buttons']:
        inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], callback_data=f"delete_link_{button['text']}"))
    for button in default_buttons:
        inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], callback_data=f"delete_link_{button['text']}"))
    
    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel"))
    bot.send_message(call.message.chat.id, "Select a link button to delete:", reply_markup=inline_keyboard)

def delete_menu_menu(message):
    logging.info(f"User {message.from_user.username} (ID: {message.from_user.id}) opened the delete menu options.")
    inline_keyboard = types.InlineKeyboardMarkup()
    for menu_name in config['menus']:
        logging.info(f"Adding menu: {menu_name} to delete options")
        inline_keyboard.add(types.InlineKeyboardButton(text=menu_name, callback_data=f"delete_menu_{menu_name}"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel"))
    bot.send_message(message.chat.id, "Select a menu to delete:", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_menu_"))
def handle_delete_menu(call):
    menu_name = call.data[len("delete_menu_"):]
    logging.info(f"User {call.from_user.username} (ID: {call.from_user.id}) selected to delete menu: {menu_name}")
    delete_menu(call.message, menu_name)

def delete_menu(message, menu_name):
    logging.info(f"User {message.from_user.username} (ID: {message.from_user.id}) attempting to delete menu: {menu_name}")
    if menu_name in config['menus']:
        del config['menus'][menu_name]
        write_config(config)
        reload_config()  # Reload configuration after writing
        bot.reply_to(message, f'Menu "{menu_name}" deleted successfully.', reply_markup=back_keyboard())
        logging.info(f"Menu {menu_name} deleted successfully.")
    else:
        bot.reply_to(message, f'Menu "{menu_name}" not found.', reply_markup=back_keyboard())
        logging.info(f"Menu {menu_name} not found.")
    
    # Hapus semua tombol inline di menu utama
    if 'custom_buttons' in config:
        config['custom_buttons'] = []
        write_config(config)
        reload_config()  # Reload configuration after writing

@bot.callback_query_handler(func=lambda call: call.data == "edit_button_name")
def handle_edit_button_name(call):
    logging.info(f"User {call.from_user.username} (ID: {call.from_user.id}) selected to edit button names.")
    inline_keyboard = types.InlineKeyboardMarkup()
    default_buttons = [
        {"text": config.get('join_my_text', "JOIN MY🇲🇾"), "url": config['join_my_url']},
        {"text": config.get('join_sg_text', "JOIN SG🇸🇬"), "url": config['join_sg_url']},
        {"text": config.get('freecr_365_text', "🤑 FREE CREDIT 🤑"), "url": config['freecr_365_url']}
    ]
    for button in default_buttons:
        inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], callback_data=f"edit_name_{button['text']}"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel"))
    bot.send_message(call.message.chat.id, "Select a button to edit its name:", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_name_"))
def handle_edit_name(call):
    button_text = call.data[len("edit_name_"):]
    logging.info(f"User {call.from_user.username} (ID: {call.from_user.id}) selected to edit name of button: {button_text}")
    msg = bot.send_message(call.message.chat.id, f"Please send the new name for the button '{button_text}':", reply_markup=back_keyboard())
    bot.register_next_step_handler(msg, lambda m: set_button_name(m, button_text))

def set_button_name(message, old_name):
    new_name = message.text
    button_text_map = {
        config.get('join_my_text', "JOIN MY🇲🇾"): "join_my_text",
        config.get('join_sg_text', "JOIN SG🇸🇬"): "join_sg_text",
        config.get('freecr_365_text', "🤑 FREE CREDIT 🤑"): "freecr_365_text"
    }
    if old_name in button_text_map:
        config[button_text_map[old_name]] = new_name
        write_config(config)
        reload_config()  # Reload configuration after writing
        logging.info(f"User {message.from_user.username} (ID: {message.from_user.id}) changed button name from '{old_name}' to '{new_name}'")
        bot.reply_to(message, f'Button name changed from "{old_name}" to "{new_name}".', reply_markup=back_keyboard())
    else:
        logging.error(f"User {message.from_user.username} (ID: {message.from_user.id}) attempted to change name of non-existent button: {old_name}")
        bot.reply_to(message, f'Button "{old_name}" not found in default buttons.', reply_markup=back_keyboard())