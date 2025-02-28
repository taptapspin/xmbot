import logging
import requests
import random
import json
from config import bot, config, bot_owner_id
from bs4 import BeautifulSoup
from telebot import types, TeleBot
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import imageio
import os
import numpy as np

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

def send_random_lottery_gif(bot, chat_id):
    giphy_api_key = 'oTvmjx3ZqxwK1daHDc3ZSYjIdKBr8EMg'
    giphy_search_url = f'https://api.giphy.com/v1/gifs/random?api_key={giphy_api_key}&tag=lottery+jackpot+winning&rating=g'

    retries = 1
    for attempt in range(retries):
        try:
            response = requests.get(giphy_search_url)
            data = response.json()
            gif_url = data['data']['images']['original']['url']
            
            # Load button settings from config
            config = load_config()
            play_now_my_text = config['button_settings']['play_now_my']['text']
            play_now_my_url = config['button_settings']['play_now_my']['url']
            play_now_sg_text = config['button_settings']['play_now_sg']['text']
            play_now_sg_url = config['button_settings']['play_now_sg']['url']
            
            # Create inline buttons
            inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
            inline_keyboard.add(
                types.InlineKeyboardButton(text=play_now_my_text, url=play_now_my_url),
                types.InlineKeyboardButton(text=play_now_sg_text, url=play_now_sg_url)
            )
            inline_keyboard.add(
                types.InlineKeyboardButton(text="🏆 4D Live Results Today 🏆", callback_data="live_results")
            )
            inline_keyboard.add(
                types.InlineKeyboardButton(text="🏅Magnum", callback_data="magnum"),
                types.InlineKeyboardButton(text="🏅DaMaCai", callback_data="damacai"),
                types.InlineKeyboardButton(text="🏅Toto", callback_data="toto")
            )
            inline_keyboard.add(
                types.InlineKeyboardButton(text="🏅Singapore 4D", callback_data="singapore_4d"),
                types.InlineKeyboardButton(text="🏅Lucky Hari-Hari", callback_data="lucky_hari_hari")
            )
            inline_keyboard.add(
                types.InlineKeyboardButton(text="🏅Sabah 4D", callback_data="sabah_4d"),
                types.InlineKeyboardButton(text="🏅Perdana 4D", callback_data="perdana_4d"),
                types.InlineKeyboardButton(text="🏅Good 4D", callback_data="good_4d")
            )
            inline_keyboard.add(
                types.InlineKeyboardButton(text="🏅Sandakan 4D", callback_data="sandakan_4d"),
                types.InlineKeyboardButton(text="🏅Sarawak 4D", callback_data="sarawak_4d")
            )
            
            # Add "Button Setting" for admins or bot owner above the "Back" button
            if chat_id in config['admins'] or chat_id == bot_owner_id:
                inline_keyboard.add(
                    types.InlineKeyboardButton(text="⚙️Button Setting⚙️", callback_data="button4d_setting")
                )
            
            inline_keyboard.add(
                types.InlineKeyboardButton(text="⬅️Back", callback_data="back")
            )
            
            # Send the random GIF with inline buttons
            bot.send_animation(chat_id, gif_url, reply_markup=inline_keyboard)
        except Exception as e:
            logging.error(f"Failed to send GIF: {e}")

def create_gif_with_number(number):
    images = []
    base_color = (212, 174, 156)  # #d4ae9c
    confetti_colors = [(255, 0, 0, 128), (0, 255, 0, 128), (0, 0, 255, 128), (255, 255, 0, 128), (255, 0, 255, 128), (0, 255, 255, 128)]  # 128 is 50% opacity
    num_confetti = 50
    confetti_positions = [(np.random.randint(0, 400), np.random.randint(0, 200)) for _ in range(num_confetti)]
    
    for i in range(10):  # Create 10 frames for the GIF
        img = Image.new('RGBA', (400, 200), color=base_color + (255,)) 
        d = ImageDraw.Draw(img)
        font = ImageFont.truetype("arial.ttf", 150)
        text = str(number)
        text_bbox = d.textbbox((0, 0), text, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        position = ((img.width - text_width) / 2, (img.height - text_height) / 2)
        
        # Create a shining effect by varying the brightness
        brightness = 1 + 0.025 * (i % 5)  # Reduced brightness variation
        enhancer = ImageEnhance.Brightness(img.convert('RGB'))
        img = enhancer.enhance(brightness).convert('RGBA')
        
        d = ImageDraw.Draw(img)
        d.text(position, text, font=font, fill=(255, 255, 255, 255))  # White text
        
        # Add confetti
        for j in range(num_confetti):
            x, y = confetti_positions[j]
            y = (y + i * 5) % 200  # Move confetti down
            color = confetti_colors[np.random.randint(0, len(confetti_colors))]
            d.rectangle([x, y, x+5, y+5], fill=color)
        
        img_path = f"frame_{i}.png"
        img.save(img_path)
        images.append(imageio.imread(img_path))
        os.remove(img_path)
    gif_path = f"{number}.gif"
    imageio.mimsave(gif_path, images, duration=0.1)
    return gif_path

def send_lucky_number(call, platform_name):
    chat_id = call.message.chat.id
    random_number = random.randint(1000, 9999)
    gif_path = create_gif_with_number(random_number)
    
    message = (
        f"Congratulations! Your lucky number for 🏅{platform_name} 🥳 has arrived, this is your lucky number: 👉 {random_number} 👈.\n\n"
        "Click the button below to place your bet now and enjoy ours highest payouts in the market!"
    )
    
    # Escape special characters for MarkdownV2
    message = message.replace('.', '\\.').replace('-', '\\-').replace('(', '\\(').replace(')', '\\)').replace('!', '\\!').replace('_', '\\_').replace('=', '\\=').replace('+', '\\+').replace('`', '\\`')

    # Load button settings from config
    config = load_config()
    play_now_my_text = config['button_settings']['play_now_my']['text']
    play_now_my_url = config['button_settings']['play_now_my']['url']
    play_now_sg_text = config['button_settings']['play_now_sg']['text']
    play_now_sg_url = config['button_settings']['play_now_sg']['url']
    
    # Create inline buttons
    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        types.InlineKeyboardButton(text=play_now_my_text, url=play_now_my_url),
        types.InlineKeyboardButton(text=play_now_sg_text, url=play_now_sg_url)
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Back", callback_data="back")
    )
    
    # Send the random GIF with message and inline buttons
    with open(gif_path, 'rb') as gif:
        bot.send_animation(chat_id, gif, caption=message, reply_markup=inline_keyboard, parse_mode='MarkdownV2')
    os.remove(gif_path)

@bot.callback_query_handler(func=lambda call: call.data in ["magnum", "damacai", "toto", "singapore_4d", "lucky_hari_hari", "sabah_4d", "perdana_4d", "good_4d", "sandakan_4d", "sarawak_4d"])
def handle_lottery_buttons(call):
    platform_name = call.data.replace("_", " ").title()
    send_lucky_number(call, platform_name)

# FUNGSI 4D LIVE RESULTS
@bot.callback_query_handler(func=lambda call: call.data == "live_results")
def show_4d_options(call):
    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(text="Magnum 4D Results", callback_data="magnum_results_4d"),
        types.InlineKeyboardButton(text="DaMaCai 4D Results", callback_data="damacai_results_4d"),
        types.InlineKeyboardButton(text="Toto 4D Results", callback_data="toto_results_4d"),
        types.InlineKeyboardButton(text="Singapore 4D Results", callback_data="singapore_results_4d"),
        types.InlineKeyboardButton(text="Lucky Hari-Hari 4D Results", callback_data="lucky_results_hari__hari_4d"),
        types.InlineKeyboardButton(text="Sabah 4D Results", callback_data="sabah_results_4d"),
        types.InlineKeyboardButton(text="Perdana 4D Results", callback_data="perdana_results_4d"),
        types.InlineKeyboardButton(text="Good 4D Results", callback_data="good_results_4d"),
        types.InlineKeyboardButton(text="Sandakan 4D Results", callback_data="sandakan_results_4d"),
        types.InlineKeyboardButton(text="Sarawak 4D Results", callback_data="sarawak_results_4d"),
        types.InlineKeyboardButton(text="Back", callback_data="back")
    ]
    
    # Arrange buttons in rows
    keyboard.add(*buttons[:2])
    keyboard.add(*buttons[2:4])
    keyboard.add(buttons[4])
    keyboard.add(*buttons[5:7])
    keyboard.add(*buttons[7:9])
    keyboard.add(buttons[9])
    keyboard.add(buttons[10])
    
    bot.send_message(call.message.chat.id, "Which 4D lottery results would you like to see?", reply_markup=keyboard)

def create_results_keyboard(chat_id):
    keyboard = types.InlineKeyboardMarkup()
    
    # Load button settings from config
    config = load_config()
    button_results_text = config['button_results']['text']
    button_results_url = config['button_results']['url']
    
    live_results_button = types.InlineKeyboardButton(text=button_results_text, url=button_results_url)
    back_button = types.InlineKeyboardButton(text="Back", callback_data="back")
    keyboard.add(live_results_button)
    
    # Load config to get admins and bot owner ID
    bot_owner_id = config.get('bot_owner_id')
    admins = config.get('admins', [])
    
    # Add the new button only for admins and bot owner
    if chat_id in admins or chat_id == bot_owner_id:
        admin_button = types.InlineKeyboardButton(text="⚙️Setting Results Button⚙️", callback_data="setting_results")
        keyboard.add(admin_button)
    
    keyboard.add(back_button)
    return keyboard

#FUNGSI RESULTS Magnum 4D
@bot.callback_query_handler(func=lambda call: call.data == "magnum_results_4d")
def show_magnum_results(call):
    url = "https://www.check4d.org/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract data
    platform_name1 = "𝗠𝗮𝗴𝗻𝘂𝗺 𝟰𝗗 萬能"
    date_div1 = soup.find('td', {'id': 'mdd'})
    date1 = date_div1.text.strip() if date_div1 else '----'
    
    first_prize_div1 = soup.find('td', {'id': 'mp1'})
    first_prize1 = first_prize_div1.text.strip() if first_prize_div1 else '----'
    
    second_prize_div1 = soup.find('td', {'id': 'mp2'})
    second_prize1 = second_prize_div1.text.strip() if second_prize_div1 else '----'
    
    third_prize_div1 = soup.find('td', {'id': 'mp3'})
    third_prize1 = third_prize_div1.text.strip() if third_prize_div1 else '----'
    
    special_numbers1 = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('ms')})] or ['----'] * 13
    consolation_numbers1 = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('mc')})] or ['----'] * 10
    
    # Format the message
    special_numbers_formatted1 = ', '.join(special_numbers1[:4]) + ',\n' + ', '.join(special_numbers1[4:8]) + ',\n' + ', '.join(special_numbers1[8:12]) + ',\n' + special_numbers1[12]
    consolation_numbers_formatted1 = ', '.join(consolation_numbers1[:4]) + ',\n' + ', '.join(consolation_numbers1[4:8]) + ',\n' + ', '.join(consolation_numbers1[8:10])
    
    result_message = f"""
Here is the result of {platform_name1}
{date1}.
🥳Congratulations to all the winners‼️

🏆1𝚜𝚝 𝙿𝚛𝚒𝚣𝚎 首獎: {first_prize1}
🏆2𝚗𝚍 𝙿𝚛𝚒𝚣𝚎 二獎: {second_prize1}
🏆3𝚛𝚍 𝙿𝚛𝚒𝚣𝚎 三獎: {third_prize1}

🏆𝚂𝚙𝚎𝚌𝚒𝚊𝚕 特別獎: 
{special_numbers_formatted1}

🏆𝙲𝚘𝚗𝚜𝚘𝚕𝚊𝚝𝚒𝚘𝚗 安慰獎: 
{consolation_numbers_formatted1}
"""
    
     # Create inline keyboard with "Live Results" and "Back" buttons
    keyboard = create_results_keyboard(call.message.chat.id)
    bot.send_message(call.message.chat.id, result_message, reply_markup=keyboard)

#FUNGSI RESULTS DaMaCai 4D
@bot.callback_query_handler(func=lambda call: call.data == "damacai_results_4d")
def show_damacai_results(call):
    url = "https://www.check4d.org/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract data
    platform2_name = "𝗗𝗮𝗠𝗮𝗖𝗮𝗶 𝟰𝗗 大馬彩"
    date_div2 = soup.find('td', {'id': 'ddd'})
    date2 = date_div2.text.strip() if date_div2 else '----'
    
    first_prize2_div = soup.find('td', {'id': 'dp1'})
    first_prize2 = first_prize2_div.text.strip() if first_prize2_div else '----'
    
    second_prize2_div = soup.find('td', {'id': 'dp2'})
    second_prize2 = second_prize2_div.text.strip() if second_prize2_div else '----'
    
    third_prize2_div = soup.find('td', {'id': 'dp3'})
    third_prize2 = third_prize2_div.text.strip() if third_prize2_div else '----'
    
    special2_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('ds')})] or ['----'] * 10
    consolation2_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('dc')})] or ['----'] * 10
    
    # Format the message
    special2_numbers_formatted = ', '.join(special2_numbers[:4]) + ',\n' + ', '.join(special2_numbers[4:8]) + ',\n' + ', '.join(special2_numbers[8:10])
    if len(special2_numbers) > 10:
        special2_numbers_formatted += ',\n' + special2_numbers[10]
    
    consolation2_numbers_formatted = ', '.join(consolation2_numbers[:4]) + ',\n' + ', '.join(consolation2_numbers[4:8]) + ',\n' + ', '.join(consolation2_numbers[8:10])
    
    result_message = f"""
Here is the result of {platform2_name}
{date2}.
🥳Congratulations to all the winners‼️

🏆1𝚜𝚝 𝙿𝚛𝚒𝚣𝚎 首獎: {first_prize2}
🏆2𝚗𝚍 𝙿𝚛𝚒𝚣𝚎 二獎: {second_prize2}
🏆3𝚛𝚍 𝙿𝚛𝚒𝚣𝚎 三獎: {third_prize2}

🏆𝚂𝚙𝚎𝚌𝚒𝚊𝚕 特別獎: 
{special2_numbers_formatted}

🏆𝙲𝚘𝚗𝚜𝚘𝚕𝚊𝚝𝚒𝚘𝚗 安慰獎: 
{consolation2_numbers_formatted}
"""
    
    # Create inline keyboard with "Back" button
    keyboard = create_results_keyboard(call.message.chat.id)
    bot.send_message(call.message.chat.id, result_message, reply_markup=keyboard)

#FUNGSI RESULTS TOTO 4D
@bot.callback_query_handler(func=lambda call: call.data == "toto_results_4d")
def show_toto_results(call):
    url = "https://www.check4d.org/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

 # Extract data
    platform3_name = "𝗧𝗼𝘁𝗼 𝟰𝗗 多多"
    date_div3 = soup.find('td', {'id': 'tdd'})
    date3 = date_div3.text.strip() if date_div3 else '----'
    
    first_prize3_div = soup.find('td', {'id': 'tp1'})
    first_prize3 = first_prize3_div.text.strip() if first_prize3_div else '----'
    
    second_prize3_div = soup.find('td', {'id': 'tp2'})
    second_prize3 = second_prize3_div.text.strip() if second_prize3_div else '----'
    
    third_prize3_div = soup.find('td', {'id': 'tp3'})
    third_prize3 = third_prize3_div.text.strip() if third_prize3_div else '----'
    
    special3_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('ts')})] or ['----'] * 13
    consolation3_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('tc')})] or ['----'] * 10

    special3_numbers_formatted = ', '.join(special3_numbers[:4]) + ',\n' + ', '.join(special3_numbers[4:8]) + ',\n' + ', '.join(special3_numbers[8:12]) + ',\n' + special3_numbers[12]
    consolation3_numbers_formatted = ', '.join(consolation3_numbers[:4]) + ',\n' + ', '.join(consolation3_numbers[4:8]) + ',\n' + ', '.join(consolation3_numbers[8:10])
   
    result_message = f"""
Here is the result of {platform3_name}
{date3}.
🥳Congratulations to all the winners‼️

🏆1𝚜𝚝 𝙿𝚛𝚒𝚣𝚎 首獎: {first_prize3}
🏆2𝚗𝚍 𝙿𝚛𝚒𝚣𝚎 二獎: {second_prize3}
🏆3𝚛𝚍 𝙿𝚛𝚒𝚣𝚎 三獎: {third_prize3}

🏆𝚂𝚙𝚎𝚌𝚒𝚊𝚕 特別獎: 
{special3_numbers_formatted}

🏆𝙲𝚘𝚗𝚜𝚘𝚕𝚊𝚝𝚒𝚘𝚗 安慰獎: 
{consolation3_numbers_formatted}
"""
    
    # Create inline keyboard with "Back" button
    keyboard = create_results_keyboard(call.message.chat.id)
    bot.send_message(call.message.chat.id, result_message, reply_markup=keyboard)

#FUNGSI RESULTS SINGAPORE 4D
@bot.callback_query_handler(func=lambda call: call.data == "singapore_results_4d")
def show_singapore_results(call):
    url = "https://www.check4d.org/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract data
    platform4_name = "𝗦𝗶𝗻𝗴𝗮𝗽𝗼𝗿𝗲𝗶 𝟰𝗗"
    date_div4 = soup.find('td', {'id': 'sdd'})
    date4 = date_div4.text.strip() if date_div4 else '----'
    
    first_prize4_div = soup.find('td', {'id': 'sp1'})
    first_prize4 = first_prize4_div.text.strip() if first_prize4_div else '----'
    
    second_prize4_div = soup.find('td', {'id': 'sp2'})
    second_prize4 = second_prize4_div.text.strip() if second_prize4_div else '----'
    
    third_prize4_div = soup.find('td', {'id': 'sp3'})
    third_prize4 = third_prize4_div.text.strip() if third_prize4_div else '----'
    
    special4_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('ss')})] or ['----'] * 10
    consolation4_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('sc')})] or ['----'] * 10
    
    # Format the message
    special4_numbers_formatted = ', '.join(special4_numbers[:4]) + ',\n' + ', '.join(special4_numbers[4:8]) + ',\n' + ', '.join(special4_numbers[8:10])
    if len(special4_numbers) > 10:
        special4_numbers_formatted += ',\n' + special4_numbers[10]
    
    consolation4_numbers_formatted = ', '.join(consolation4_numbers[:4]) + ',\n' + ', '.join(consolation4_numbers[4:8]) + ',\n' + ', '.join(consolation4_numbers[8:10])
    
    result_message = f"""
Here is the result of {platform4_name}
{date4}.
🥳Congratulations to all the winners‼️

🏆1𝚜𝚝 𝙿𝚛𝚒𝚣𝚎 首獎: {first_prize4}
🏆2𝚗𝚍 𝙿𝚛𝚒𝚣𝚎 二獎: {second_prize4}
🏆3𝚛𝚍 𝙿𝚛𝚒𝚣𝚎 三獎: {third_prize4}

🏆𝚂𝚙𝚎𝚌𝚒𝚊𝚕 特別獎: 
{special4_numbers_formatted}

🏆𝙲𝚘𝚗𝚜𝚘𝚕𝚊𝚝𝚒𝚘𝚗 安慰獎: 
{consolation4_numbers_formatted}
"""
    
    # Create inline keyboard with "Back" button
    keyboard = create_results_keyboard(call.message.chat.id)
    bot.send_message(call.message.chat.id, result_message, reply_markup=keyboard)

#FUNGSI RESULTS LUCKY HARI-HARI 4D
@bot.callback_query_handler(func=lambda call: call.data == "lucky_results_hari__hari_4d")
def show_lucky_hari_hari_results(call):
    url = "https://www.check4d.org/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

 # Extract data
    platform5_name = "𝗟𝘂𝗰𝗸𝘆 𝗛𝗮𝗿𝗶 - 𝗛𝗮𝗿𝗶 𝟰𝗗 天天好运"
    date_div5 = soup.find('td', {'id': 'hdd'})
    date5 = date_div5.text.strip() if date_div5 else '----'
    
    first_prize5_div = soup.find('td', {'id': 'hp1'})
    first_prize5 = first_prize5_div.text.strip() if first_prize5_div else '----'
    
    second_prize5_div = soup.find('td', {'id': 'hp2'})
    second_prize5 = second_prize5_div.text.strip() if second_prize5_div else '----'
    
    third_prize5_div = soup.find('td', {'id': 'hp3'})
    third_prize5 = third_prize5_div.text.strip() if third_prize5_div else '----'
    
    special5_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('hs')})] or ['----'] * 13
    consolation5_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('hc')})] or ['----'] * 10

    special5_numbers_formatted = ', '.join(special5_numbers[:4]) + ',\n' + ', '.join(special5_numbers[4:8]) + ',\n' + ', '.join(special5_numbers[8:12]) + ',\n' + special5_numbers[12]
    consolation5_numbers_formatted = ', '.join(consolation5_numbers[:4]) + ',\n' + ', '.join(consolation5_numbers[4:8]) + ',\n' + ', '.join(consolation5_numbers[8:10])
   
    result_message = f"""
Here is the result of {platform5_name}
{date5}.
🥳Congratulations to all the winners‼️

🏆1𝚜𝚝 𝙿𝚛𝚒𝚣𝚎 首獎: {first_prize5}
🏆2𝚗𝚍 𝙿𝚛𝚒𝚣𝚎 二獎: {second_prize5}
🏆3𝚛𝚍 𝙿𝚛𝚒𝚣𝚎 三獎: {third_prize5}

🏆𝚂𝚙𝚎𝚌𝚒𝚊𝚕 特別獎: 
{special5_numbers_formatted}

🏆𝙲𝚘𝚗𝚜𝚘𝚕𝚊𝚝𝚒𝚘𝚗 安慰獎: 
{consolation5_numbers_formatted}
"""
    
    # Create inline keyboard with "Back" button
    keyboard = create_results_keyboard(call.message.chat.id)
    bot.send_message(call.message.chat.id, result_message, reply_markup=keyboard)  

#FUNGSI RESULTS SABAH 4D
@bot.callback_query_handler(func=lambda call: call.data == "sabah_results_4d")
def show_sabah_results(call):
    url = "https://www.check4d.org/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

 # Extract data
    platform6_name = "𝗦𝗮𝗯𝗮𝗵 𝟰𝗗 沙巴萬字"
    date_div6 = soup.find('td', {'id': 'sbdd'})
    date6 = date_div6.text.strip() if date_div6 else '----'
    
    first_prize6_div = soup.find('td', {'id': 'sbp1'})
    first_prize6 = first_prize6_div.text.strip() if first_prize6_div else '----'
    
    second_prize6_div = soup.find('td', {'id': 'sbp2'})
    second_prize6 = second_prize6_div.text.strip() if second_prize6_div else '----'
    
    third_prize6_div = soup.find('td', {'id': 'sbp3'})
    third_prize6 = third_prize6_div.text.strip() if third_prize6_div else '----'
    
    special6_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('sbs')})] or ['----'] * 13
    consolation6_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('sbc')})] or ['----'] * 10

    special6_numbers_formatted = ', '.join(special6_numbers[:4]) + ',\n' + ', '.join(special6_numbers[4:8]) + ',\n' + ', '.join(special6_numbers[8:12]) + ',\n' + special6_numbers[12]
    consolation6_numbers_formatted = ', '.join(consolation6_numbers[:4]) + ',\n' + ', '.join(consolation6_numbers[4:8]) + ',\n' + ', '.join(consolation6_numbers[8:10])
   
    result_message = f"""
Here is the result of {platform6_name}
{date6}.
🥳Congratulations to all the winners‼️

🏆1𝚜𝚝 𝙿𝚛𝚒𝚣𝚎 首獎: {first_prize6}
🏆2𝚗𝚍 𝙿𝚛𝚒𝚣𝚎 二獎: {second_prize6}
🏆3𝚛𝚍 𝙿𝚛𝚒𝚣𝚎 三獎: {third_prize6}

🏆𝚂𝚙𝚎𝚌𝚒𝚊𝚕 特別獎: 
{special6_numbers_formatted}

🏆𝙲𝚘𝚗𝚜𝚘𝚕𝚊𝚝𝚒𝚘𝚗 安慰獎: 
{consolation6_numbers_formatted}
"""
    
    # Create inline keyboard with "Back" button
    keyboard = create_results_keyboard(call.message.chat.id)
    bot.send_message(call.message.chat.id, result_message, reply_markup=keyboard) 

#FUNGSI RESULTS PERDANA 4D
@bot.callback_query_handler(func=lambda call: call.data == "perdana_results_4d")
def show_perdana_results(call):
    url = "https://www.check4d.org/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

 # Extract data
    platform7_name = "𝗣𝗲𝗿𝗱𝗮𝗻𝗮 𝟰𝗗"
    date_div7 = soup.find('td', {'id': 'pdd'})
    date7 = date_div7.text.strip() if date_div7 else '----'
    
    first_prize7_div = soup.find('td', {'id': 'pp1'})
    first_prize7 = first_prize7_div.text.strip() if first_prize7_div else '----'
    
    second_prize7_div = soup.find('td', {'id': 'pp2'})
    second_prize7 = second_prize7_div.text.strip() if second_prize7_div else '----'
    
    third_prize7_div = soup.find('td', {'id': 'pp3'})
    third_prize7 = third_prize7_div.text.strip() if third_prize7_div else '----'
    
    special7_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('ps')})] or ['----'] * 13
    consolation7_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('pc')})] or ['----'] * 10

    special7_numbers_formatted = ', '.join(special7_numbers[:4]) + ',\n' + ', '.join(special7_numbers[4:8]) + ',\n' + ', '.join(special7_numbers[8:12]) + ',\n' + special7_numbers[12]
    consolation7_numbers_formatted = ', '.join(consolation7_numbers[:4]) + ',\n' + ', '.join(consolation7_numbers[4:8]) + ',\n' + ', '.join(consolation7_numbers[8:10])
   
    result_message = f"""
Here is the result of {platform7_name}
{date7}.
🥳Congratulations to all the winners‼️

🏆1𝚜𝚝 𝙿𝚛𝚒𝚣𝚎 首獎: {first_prize7}
🏆2𝚗𝚍 𝙿𝚛𝚒𝚣𝚎 二獎: {second_prize7}
🏆3𝚛𝚍 𝙿𝚛𝚒𝚣𝚎 三獎: {third_prize7}

🏆𝚂𝚙𝚎𝚌𝚒𝚊𝚕 特別獎: 
{special7_numbers_formatted}

🏆𝙲𝚘𝚗𝚜𝚘𝚕𝚊𝚝𝚒𝚘𝚗 安慰獎: 
{consolation7_numbers_formatted}
"""
    
    # Create inline keyboard with "Back" button
    keyboard = create_results_keyboard(call.message.chat.id)
    bot.send_message(call.message.chat.id, result_message, reply_markup=keyboard)   
    
#FUNGSI RESULTS GOOD 4D UNDER PROGRESS
@bot.callback_query_handler(func=lambda call: call.data == "good_results_4d")
def show_singapore_results(call):
    url = "https://4dlives.com/en/good4d"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract data
    platform8_name = "𝗚𝗼𝗼𝗱 𝟰𝗗 好的"
    date_div8 = soup.find('span', {'class': 'is-size-6 is-size-7-mobile'})
    date8 = date_div8.text.strip() if date_div8 else '----'
    
    first_prize8_div = soup.find('td', {'id': 'aG_1'})
    first_prize8 = first_prize8_div.text.strip() if first_prize8_div else '----'
    
    second_prize8_div = soup.find('td', {'class' : 'popwin','id' : 'aG_1'})
    second_prize8 = second_prize8_div.text.strip() if second_prize8_div else '----'
    
    third_prize8_div = soup.find('td', {'class': 'is-size-4 has-text-centered"'})
    third_prize8 = third_prize8_div.text.strip() if third_prize8_div else '----'
    
    special8_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('ss')})] or ['----'] * 10
    consolation8_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('sc')})] or ['----'] * 10
    
    # Format the message
    special8_numbers_formatted = ', '.join(special8_numbers[:4]) + ',\n' + ', '.join(special8_numbers[4:8]) + ',\n' + ', '.join(special8_numbers[8:10])
    if len(special8_numbers) > 10:
        special8_numbers_formatted += ',\n' + special8_numbers[10]
    
    consolation8_numbers_formatted = ', '.join(consolation8_numbers[:4]) + ',\n' + ', '.join(consolation8_numbers[4:8]) + ',\n' + ', '.join(consolation8_numbers[8:10])
    
    result_message = f"""
Here is the result of {platform8_name}
{date8}.
🥳Congratulations to all the winners‼️

🏆1𝚜𝚝 𝙿𝚛𝚒𝚣𝚎 首獎: {first_prize8}
🏆2𝚗𝚍 𝙿𝚛𝚒𝚣𝚎 二獎: {second_prize8}
🏆3𝚛𝚍 𝙿𝚛𝚒𝚣𝚎 三獎: {third_prize8}

🏆𝚂𝚙𝚎𝚌𝚒𝚊𝚕 特別獎: 
{special8_numbers_formatted}

🏆𝙲𝚘𝚗𝚜𝚘𝚕𝚊𝚝𝚒𝚘𝚗 安慰獎: 
{consolation8_numbers_formatted}
"""
    
    # Create inline keyboard with "Back" button
    keyboard = create_results_keyboard(call.message.chat.id)
    bot.send_message(call.message.chat.id, result_message, reply_markup=keyboard)

#FUNGSI RESULTS SANDAKAN 4D
@bot.callback_query_handler(func=lambda call: call.data == "sandakan_results_4d")
def show_sandakan_results(call):
    url = "https://www.check4d.org/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

 # Extract data
    platform9_name = "𝗦𝗮𝗻𝗱𝗮𝗸𝗮𝗻 𝟰𝗗 山打根赛马会"
    date_div9 = soup.find('td', {'id': 'stdd'})
    date9 = date_div9.text.strip() if date_div9 else '----'
    
    first_prize9_div = soup.find('td', {'id': 'stp1'})
    first_prize9 = first_prize9_div.text.strip() if first_prize9_div else '----'
    
    second_prize9_div = soup.find('td', {'id': 'stp2'})
    second_prize9 = second_prize9_div.text.strip() if second_prize9_div else '----'
    
    third_prize9_div = soup.find('td', {'id': 'stp3'})
    third_prize9 = third_prize9_div.text.strip() if third_prize9_div else '----'
    
    special9_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('sts')})] or ['----'] * 13
    consolation9_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('stc')})] or ['----'] * 10

    special9_numbers_formatted = ', '.join(special9_numbers[:4]) + ',\n' + ', '.join(special9_numbers[4:8]) + ',\n' + ', '.join(special9_numbers[8:12]) + ',\n' + special9_numbers[12]
    consolation9_numbers_formatted = ', '.join(consolation9_numbers[:4]) + ',\n' + ', '.join(consolation9_numbers[4:8]) + ',\n' + ', '.join(consolation9_numbers[8:10])
   
    result_message = f"""
Here is the result of {platform9_name}
{date9}.
🥳Congratulations to all the winners‼️

🏆1𝚜𝚝 𝙿𝚛𝚒𝚣𝚎 首獎: {first_prize9}
🏆2𝚗𝚍 𝙿𝚛𝚒𝚣𝚎 二獎: {second_prize9}
🏆3𝚛𝚍 𝙿𝚛𝚒𝚣𝚎 三獎: {third_prize9}

🏆𝚂𝚙𝚎𝚌𝚒𝚊𝚕 特別獎: 
{special9_numbers_formatted}

🏆𝙲𝚘𝚗𝚜𝚘𝚕𝚊𝚝𝚒𝚘𝚗 安慰獎: 
{consolation9_numbers_formatted}
"""
    
    # Create inline keyboard with "Back" button
    keyboard = create_results_keyboard(call.message.chat.id)
    bot.send_message(call.message.chat.id, result_message, reply_markup=keyboard)     

#FUNGSI RESULTS SARAWAK 4D
@bot.callback_query_handler(func=lambda call: call.data == "sarawak_results_4d")
def show_sarawak_results(call):
    url = "https://www.check4d.org/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract data
    platform10_name = "𝗦𝗮𝗿𝗮𝘄𝗮𝗸 𝟰𝗗 砂勞越大萬"
    date_div10 = soup.find('td', {'id': 'swdd'})
    date10 = date_div10.text.strip() if date_div10 else '----'
    
    first_prize10_div = soup.find('td', {'id': 'swp1'})
    first_prize10 = first_prize10_div.text.strip() if first_prize10_div else '----'
    
    second_prize10_div = soup.find('td', {'id': 'swp2'})
    second_prize10 = second_prize10_div.text.strip() if second_prize10_div else '----'
    
    third_prize10_div = soup.find('td', {'id': 'swp3'})
    third_prize10 = third_prize10_div.text.strip() if third_prize10_div else '----'
    
    special10_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('sws')})] or ['----'] * 10
    consolation10_numbers = [div.text.strip() for div in soup.find_all('td', {'id': lambda x: x and x.startswith('swc')})] or ['----'] * 10
    
    # Format the message
    special10_numbers_formatted = ', '.join(special10_numbers[:4]) + ',\n' + ', '.join(special10_numbers[4:8]) + ',\n' + ', '.join(special10_numbers[8:10])
    if len(special10_numbers) > 10:
        special10_numbers_formatted += ',\n' + special10_numbers[10]
    
    consolation10_numbers_formatted = ', '.join(consolation10_numbers[:4]) + ',\n' + ', '.join(consolation10_numbers[4:8]) + ',\n' + ', '.join(consolation10_numbers[8:10])
    
    result_message = f"""
Here is the result of {platform10_name}
{date10}.
🥳Congratulations to all the winners‼️

🏆1𝚜𝚝 𝙿𝚛𝚒𝚣𝚎 首獎: {first_prize10}
🏆2𝚗𝚍 𝙿𝚛𝚒𝚣𝚎 二獎: {second_prize10}
🏆3𝚛𝚍 𝙿𝚛𝚒𝚣𝚎 三獎: {third_prize10}

🏆𝚂𝚙𝚎𝚌𝚒𝚊𝚕 特別獎: 
{special10_numbers_formatted}

🏆𝙲𝚘𝚗𝚜𝚘𝚕𝚊𝚝𝚒𝚘𝚗 安慰獎: 
{consolation10_numbers_formatted}
"""
    
    # Create inline keyboard with "Back" button
    keyboard = create_results_keyboard(call.message.chat.id)
    bot.send_message(call.message.chat.id, result_message, reply_markup=keyboard)
    

#Handle Settings Buttons part1
def handle_button_setting(bot, chat_id):
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Change Button Name", callback_data="change_button_name"),
        types.InlineKeyboardButton(text="Change Button Link", callback_data="change_button_link")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Back", callback_data="back")
    )
    bot.send_message(chat_id, "4D Register Button Setting", reply_markup=inline_keyboard)

def handle_change_button_name(bot, chat_id):
    config = load_config()
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        types.InlineKeyboardButton(text=config['button_settings']['play_now_my']['text'], callback_data="change_name_play_now_my"),
        types.InlineKeyboardButton(text=config['button_settings']['play_now_sg']['text'], callback_data="change_name_play_now_sg")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Back", callback_data="back")
    )
    bot.send_message(chat_id, "Which button name do you want to change?", reply_markup=inline_keyboard)

def handle_change_button_link(bot, chat_id):
    config = load_config()
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        types.InlineKeyboardButton(text=config['button_settings']['play_now_my']['text'], callback_data="change_link_play_now_my"),
        types.InlineKeyboardButton(text=config['button_settings']['play_now_sg']['text'], callback_data="change_link_play_now_sg")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Back", callback_data="back")
    )
    bot.send_message(chat_id, "Which button link do you want to change?", reply_markup=inline_keyboard)

def update_button_name(bot, chat_id, button_key, new_name):
    config = load_config()
    config['button_settings'][button_key]['text'] = new_name
    save_config(config)
    bot.send_message(chat_id, f"Button name updated to: {new_name}")
    send_random_lottery_gif(bot, chat_id)  

def update_button_link(bot, chat_id, button_key, new_link):
    config = load_config()
    config['button_settings'][button_key]['url'] = new_link
    save_config(config)
    bot.send_message(chat_id, f"Button link updated to: {new_link}")
    send_random_lottery_gif(bot, chat_id) 

@bot.callback_query_handler(func=lambda call: call.data == "button4d_setting")
def callback_button_setting(call):
    handle_button_setting(bot, call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "change_button_name")
def callback_change_button_name(call):
    handle_change_button_name(bot, call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "change_button_link")
def callback_change_button_link(call):
    handle_change_button_link(bot, call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_name_"))
def callback_update_button_name(call):
    button_key = call.data.replace("change_name_", "")
    msg = bot.send_message(call.message.chat.id, "Please enter the new button name:")
    bot.register_next_step_handler(msg, lambda message: update_button_name(bot, call.message.chat.id, button_key, message.text))

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_link_"))
def callback_update_button_link(call):
    button_key = call.data.replace("change_link_", "")
    msg = bot.send_message(call.message.chat.id, "Please enter the new button link:")
    bot.register_next_step_handler(msg, lambda message: update_button_link(bot, call.message.chat.id, button_key, message.text))  

#Fungsi Settings Button Live Results
@bot.callback_query_handler(func=lambda call: call.data == "setting_results")
def handle_setting_results(call):
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Change Button Name", callback_data="change_live_result_button_name"),
        types.InlineKeyboardButton(text="Change Button Link", callback_data="change_live_result_button_link")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Back", callback_data="back")
    )
    bot.send_message(call.message.chat.id, "Settings Button", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "change_live_result_button_name")
def change_live_result_button_name(call):
    msg = bot.send_message(call.message.chat.id, "Please enter the new button name:")
    bot.register_next_step_handler(msg, update_live_result_button_name)

def update_live_result_button_name(message):
    new_name = message.text
    config = load_config()
    config['button_results']['text'] = new_name
    save_config(config)
    bot.send_message(message.chat.id, f"Button name updated to: {new_name}")
    send_random_lottery_gif(bot, message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "change_live_result_button_link")
def change_live_result_button_link(call):
    msg = bot.send_message(call.message.chat.id, "Please enter the new button link:")
    bot.register_next_step_handler(msg, update_live_result_button_link)

def update_live_result_button_link(message):
    new_link = message.text
    config = load_config()
    config['button_results']['url'] = new_link
    save_config(config)
    bot.send_message(message.chat.id, f"Button link updated to: {new_link}")    
    send_random_lottery_gif(bot, message.chat.id)