import telebot
from telebot import types
import os
import json
from config import bot, config, save_config, back_keyboard, bot_owner_id
from xbot4 import send_post2
from xbot5 import send_post3

@bot.callback_query_handler(func=lambda call: call.data == "add_menu")
def handle_add_menu(call):
    msg = bot.send_message(call.message.chat.id, "Please send the menu name.", reply_markup=back_keyboard())
    bot.register_next_step_handler(msg, add_menu)

def add_menu(message):
    menu_name = message.text
    config['menus'][menu_name] = {'caption': '', 'media_type': '', 'media_path': '', 'buttons': []}
    save_config()
    bot.reply_to(message, f'Menu "{menu_name}" added successfully.', reply_markup=back_keyboard())
    show_menu_settings(message, menu_name)

def show_menu_settings(message, menu_name):
    keyboard = types.InlineKeyboardMarkup()
    new_post_button = types.InlineKeyboardButton(text="New Post", callback_data=f"new_post_{menu_name}")
    edit_media_button = types.InlineKeyboardButton(text="Edit Media", callback_data=f"edit_media_{menu_name}")
    edit_caption_button = types.InlineKeyboardButton(text="Edit Caption", callback_data=f"edit_caption_{menu_name}")
    add_link_button = types.InlineKeyboardButton(text="Add Link Button", callback_data=f"add_link_button_{menu_name}")
    edit_link_button = types.InlineKeyboardButton(text="Edit Link Button", callback_data=f"edit_link_button_{menu_name}")
    remove_link_button = types.InlineKeyboardButton(text="Remove Link Button", callback_data=f"remove_link_button_{menu_name}")    
    delete_menu_button = types.InlineKeyboardButton(text="Delete Menu", callback_data=f"delete_menu_{menu_name}")
    cancel_button = types.InlineKeyboardButton(text="Cancel", callback_data="cancel")
    
    keyboard.add(new_post_button)
    keyboard.row(edit_media_button, edit_caption_button)
    keyboard.add(add_link_button)
    keyboard.row(edit_link_button, remove_link_button)
    keyboard.add(delete_menu_button)
    keyboard.add(cancel_button)
    
    bot.send_message(message.chat.id, f"Settings for menu '{menu_name}':", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("new_post_"))
def handle_new_post(call):
    menu_name = call.data[len("new_post_"):]
    msg = bot.send_message(call.message.chat.id, f"Please send the new post media (photo or video) for menu '{menu_name}'.", reply_markup=back_keyboard())
    bot.register_next_step_handler(msg, lambda m: set_new_post_media(m, menu_name))

def set_new_post_media(message, menu_name):
    if message.content_type in ['photo', 'video']:
        file_info = bot.get_file(message.photo[-1].file_id if message.content_type == 'photo' else message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Get the media path from config.py
        media_base_path = os.path.normpath(config['media_path'])
        media_path = os.path.join(media_base_path, f'{menu_name}_media')
        
        with open(media_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        config['menus'][menu_name]['media_type'] = message.content_type
        config['menus'][menu_name]['media_path'] = media_path
        save_config()
        
        bot.reply_to(message, f'New post media for menu "{menu_name}" updated successfully.', reply_markup=back_keyboard())
        send_edit_menu_preview(message.chat.id, menu_name)
    else:
        bot.reply_to(message, 'Invalid media type. Please send a photo or video.', reply_markup=back_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_media_"))
def handle_edit_media(call):
    menu_name = call.data[len("edit_media_"):]
    msg = bot.send_message(call.message.chat.id, f"Please send the new media (photo or video) for menu '{menu_name}'.", reply_markup=back_keyboard())
    bot.register_next_step_handler(msg, lambda m: set_new_post_media(m, menu_name))

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_caption_"))
def handle_edit_caption(call):
    menu_name = call.data[len("edit_caption_"):]
    msg = bot.send_message(call.message.chat.id, f"Please send the new caption for menu '{menu_name}'.", reply_markup=back_keyboard())
    bot.register_next_step_handler(msg, lambda m: set_caption(m, menu_name))

def set_caption(message, menu_name):
    config['menus'][menu_name]['caption'] = message.text
    save_config()
    bot.reply_to(message, f'Caption for menu "{menu_name}" updated successfully.', reply_markup=back_keyboard())
    send_edit_menu_preview(message.chat.id, menu_name)

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_link_button_"))
def handle_add_link_button_callback(call):
    handle_add_link_button(call)

def handle_add_link_button(call):
    menu_name = call.data[len("add_link_button_"):]
    msg = bot.send_message(call.message.chat.id, f"Please send the button text and URL in the format: Button text - URL. For multiple buttons in a row, separate them with ' | '.", reply_markup=back_keyboard())
    bot.register_next_step_handler(msg, lambda m: save_link_button(m, menu_name))

def save_link_button(message, menu_name):
    try:
        inline_keyboard = types.InlineKeyboardMarkup()
        rows = message.text.split('\n')
        
        for row in rows:
            buttons = row.split(' | ')
            inline_buttons = [types.InlineKeyboardButton(text=btn.split(' - ')[0].strip(), url=btn.split(' - ')[1].strip()) for btn in buttons]
            inline_keyboard.row(*inline_buttons)
            
            for btn in buttons:
                text, url = btn.split(' - ')
                button = {'text': text.strip(), 'url': url.strip(), 'type': 'row'}  # Default to horizontal
                if menu_name not in config['menus']:
                    bot.reply_to(message, f'Menu "{menu_name}" not found.', reply_markup=back_keyboard())
                    return
                config['menus'][menu_name]['buttons'].append(button)
        
        save_config()
        bot.reply_to(message, f'Link buttons added successfully to menu "{menu_name}".', reply_markup=back_keyboard())
        send_edit_menu_preview(message.chat.id, menu_name)
    except ValueError:
        bot.reply_to(message, 'Invalid format. Please use the format "Button text - URL". For multiple buttons in a row, separate them with " | ".', reply_markup=back_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_link_button_"))
def handle_edit_link_button(call):
    menu_name = call.data[len("edit_link_button_"):]
    inline_keyboard = types.InlineKeyboardMarkup()
    for button in config['menus'][menu_name]['buttons']:
        inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], callback_data=f"edit_link_{menu_name}_{button['text']}"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel"))
    bot.send_message(call.message.chat.id, f"Select the link button to edit for menu '{menu_name}':", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_link_"))
def handle_edit_link(call):
    data = call.data.split('_')
    menu_name = data[2]
    button_text = '_'.join(data[3:])
    msg = bot.send_message(call.message.chat.id, f"Please send the new URL for the link button '{button_text}' in menu '{menu_name}':", reply_markup=back_keyboard())
    bot.register_next_step_handler(msg, lambda m: save_edited_link(m, menu_name, button_text))

def save_edited_link(message, menu_name, button_text):
    new_url = message.text.strip()
    for button in config['menus'][menu_name]['buttons']:
        if button['text'] == button_text:
            button['url'] = new_url
            save_config()
            bot.reply_to(message, f'Link button "{button_text}" updated successfully.', reply_markup=back_keyboard())
            send_edit_menu_preview(message.chat.id, menu_name)
            return
    bot.reply_to(message, 'Button not found.', reply_markup=back_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_link_button_"))
def handle_remove_link_button(call):
    menu_name = call.data[len("remove_link_button_"):]
    inline_keyboard = types.InlineKeyboardMarkup()
    for button in config['menus'][menu_name]['buttons']:
        inline_keyboard.add(types.InlineKeyboardButton(text=button['text'], callback_data=f"remove_link_{menu_name}_{button['text']}"))
    inline_keyboard.add(types.InlineKeyboardButton(text="Cancel", callback_data="cancel"))
    bot.send_message(call.message.chat.id, f"Select the link button to remove for menu '{menu_name}':", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_link_"))
def handle_remove_link(call):
    data = call.data.split('_')
    menu_name = data[2]
    button_text = '_'.join(data[3:])
    for button in config['menus'][menu_name]['buttons']:
        if button['text'] == button_text:
            config['menus'][menu_name]['buttons'].remove(button)
            save_config()
            bot.reply_to(call.message, f'Link button "{button_text}" removed successfully.', reply_markup=back_keyboard())
            send_edit_menu_preview(call.message.chat.id, menu_name)
            return
    bot.reply_to(call.message, 'Button not found.', reply_markup=back_keyboard())

def send_edit_menu_preview(chat_id, menu_name):
    if menu_name not in config['menus']:
        bot.send_message(chat_id, f"Menu '{menu_name}' does not exist.", reply_markup=back_keyboard())
        return

    menu = config['menus'][menu_name]
    media_path = menu['media_path']
    caption = menu['caption']
    try:
        with open(media_path, 'rb') as media:
            inline_keyboard = types.InlineKeyboardMarkup()
            
            # Add all saved buttons in rows
            buttons = menu.get('buttons', [])
            for i in range(0, len(buttons), 2):
                row_buttons = buttons[i:i+2]
                inline_buttons = []
                for button in row_buttons:
                    if 'text' in button and 'url':
                        inline_buttons.append(types.InlineKeyboardButton(text=button['text'], url=button['url']))
                    elif 'name' in button:
                        inline_buttons.append(types.InlineKeyboardButton(text=button['name'], callback_data=f"menu_{button['unique_id']}"))
                inline_keyboard.row(*inline_buttons)
            
            # Add Special Bonus button for all users
            live_withdrawal_button = types.InlineKeyboardButton(text="💸 Live Withdrawal Updates 🔄", callback_data="live_withdrawal")
            inline_keyboard.row(live_withdrawal_button)

            special_bonus_button = types.InlineKeyboardButton(text=config.get('special_bonus_button_name', "Special Bonus"), callback_data="special_bonus")
            inline_keyboard.add(special_bonus_button)

            # Add Edit button if user is admin or owner
            if chat_id in config['admins'] or chat_id == bot_owner_id:
                edit_special_bonus_button = types.InlineKeyboardButton(text="Edit Button Name", callback_data="edit_special_bonus_button")
                inline_keyboard.add(edit_special_bonus_button)
                edit_button = types.InlineKeyboardButton(text="Settings", callback_data=f"edit_post_{menu_name}")
                inline_keyboard.add(edit_button)
            
            # Add Back button for all users
            back_button = types.InlineKeyboardButton(text="Back", callback_data="back")
            inline_keyboard.add(back_button)
            
            # Send media along with inline buttons
            if menu['media_type'] == 'video':
                bot.send_video(chat_id, media, caption=caption, reply_markup=inline_keyboard)
            else:
                bot.send_photo(chat_id, media, caption=caption, reply_markup=inline_keyboard)
    except FileNotFoundError:
        bot.send_message(chat_id, 'Sorry, the media file is not available.', reply_markup=back_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "special_bonus")
def handle_special_bonus(call):
    chat_id = call.message.chat.id
    send_post2(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "live_withdrawal")
def handle_live_withdrawal(call):
    chat_id = call.message.chat.id
    send_post3(chat_id)    
    
@bot.callback_query_handler(func=lambda call: call.data == "edit_special_bonus_button")
def handle_edit_special_bonus_button(call):
    msg = bot.send_message(call.message.chat.id, "Please send the new name for the 'Special Bonus' button.", reply_markup=back_keyboard())
    bot.register_next_step_handler(msg, save_special_bonus_button_name)

def save_special_bonus_button_name(message):
    new_name = message.text.strip()
    config['special_bonus_button_name'] = new_name
    save_config()
    bot.reply_to(message, f"The 'Special Bonus' button name has been updated to '{new_name}'.", reply_markup=back_keyboard())
    send_main_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def handle_back(call):
    chat_id = call.message.chat.id
    # Hapus pesan saat ini
    bot.delete_message(chat_id, call.message.message_id)
    # Optionally, you can send a new message or perform another action here

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_post_"))
def handle_edit_post(call):
    menu_name = call.data[len("edit_post_"):]
    show_menu_settings(call.message, menu_name)

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def handle_main_menu(call):
    send_main_menu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu(call):
    menu_name = call.data[len("menu_"):]
    send_edit_menu_preview(call.message.chat.id, menu_name)

@bot.callback_query_handler(func=lambda call: call.data == "start")
def handle_start(call):
    send_main_menu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def handle_cancel(call):
    # Kembali ke menu sebelumnya atau membatalkan aksi
    bot.answer_callback_query(call.id, "Action cancelled.")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_menu_"))
def handle_delete_menu(call):
    menu_name = call.data[len("delete_menu_"):]
    if menu_name in config['menus']:
        del config['menus'][menu_name]
        save_config()
        bot.reply_to(call.message, f'Menu "{menu_name}" deleted successfully.', reply_markup=back_keyboard())
    else:
        bot.reply_to(call.message, f'Menu "{menu_name}" not found.', reply_markup=back_keyboard())

def send_main_menu(chat_id):
    # Implementasikan fungsi untuk menampilkan menu utama di sini
    # Misalnya, menampilkan postingan utama atau menu utama
    main_menu_keyboard = types.InlineKeyboardMarkup()
    for menu_name in config['menus']:
        main_menu_keyboard.add(types.InlineKeyboardButton(text=menu_name, callback_data=f"menu_{menu_name}"))
    bot.send_message(chat_id, "Main Menu:", reply_markup=main_menu_keyboard)