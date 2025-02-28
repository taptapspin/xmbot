import os
import json
import logging
import uuid
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import bot, config, bot_owner_id, bot_admin_ids
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_post3(chat_id):
    gif_url = "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExYTR0ajF0Y2Q0YzRnZWxxNGRwbmFqc3Bsbmxmd2xidXZnN2JnbDJvdCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/PIdyzBZ8XiKQWfgwYk/giphy.gif"
    
    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(text="Live Withdrawal🇲🇾", callback_data="live_withdrawal_my"),
        InlineKeyboardButton(text="Live Withdrawal🇸🇬", callback_data="live_withdrawal_sg")
    )
    inline_keyboard.add(
        InlineKeyboardButton(text="Play Now MY🇲🇾", url="https://t.me/ecwon8_bot/ec8my"),
        InlineKeyboardButton(text="Play Now Sg🇸🇬", url="https://t.me/ecwon8_bot/ec8sg")
    )
    inline_keyboard.add(InlineKeyboardButton(text="Live Chat💬", url="https://t.me/ecwon8_bot/ec8lc"))
    inline_keyboard.add(InlineKeyboardButton(text="Back", callback_data="back"))
    
    caption = (
        "✨ Tap the button below to check out the latest 9 live winning transactions/withdrawals at 𝗘𝗖𝗪𝗢𝗡! 💸\n"
        "Let’s keep the winning streak going! 🎉"
    )
    
    bot.send_animation(chat_id, gif_url, caption=caption, reply_markup=inline_keyboard)
    logging.info(f"send_post3 called by user_id: {chat_id}")

@bot.callback_query_handler(func=lambda call: call.data == "live_withdrawal_my")
def handle_live_withdrawal_my(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    logging.info(f"live_withdrawal_my requested by user_id: {user_id}, username: {username}")
    
    url = 'https://ecwon88.com/en/home'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('div', {'id': 'v2cashfeed'}).find('table')
    rows = table.find('tbody').find_all('tr')[:9]
    
    withdrawals = []
    for row in rows:
        cols = row.find_all('td')
        player = cols[0].text.strip()
        withdraw = cols[3].text.strip()
        withdrawals.append(f"𝗨𝘀𝗲𝗿 𝗜𝗗: {player}\n𝗔𝗺𝗼𝘂𝗻𝘁: {withdraw}\n")
    
    now = datetime.now()
    date_str = now.strftime("%d/%m/%y")
    time_str = now.strftime("%H:%M")
    
    message = (
        "𝗖𝗼𝗻𝗴𝗿𝗮𝘁𝘂𝗹𝗮𝘁𝗶𝗼𝗻𝘀 𝘁𝗼 𝗮𝗹𝗹 𝗘𝗖𝗪𝗢𝗡 𝘄𝗶𝗻𝗻𝗲𝗿𝘀🎉\n"
        "Below is the live update of the last 9 winning transactions/withdrawals at 𝗘𝗖𝗪𝗢𝗡, updated as of "
        f"{date_str} - {time_str}\n\n" +
        "\n".join(withdrawals)
    )
    
    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(text="Play Now MY🇲🇾", url="https://t.me/ecwon8_bot/ec8my"),
        InlineKeyboardButton(text="Play Now Sg🇸🇬", url="https://t.me/ecwon8_bot/ec8sg")
    )
    inline_keyboard.add(InlineKeyboardButton(text="Back", callback_data="back"))
    
    gif_url = "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzdyNWRsdWQ0aTNycTc4ZTk3ZHBvNDB3eXZhOXI0bHM2c2RnMDZheSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/1lDFkU6NvBhsDRwSG4/giphy.gif"
    
    bot.send_animation(chat_id, gif_url, caption=message, reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "live_withdrawal_sg")
def handle_live_withdrawal_sg(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    logging.info(f"live_withdrawal_sg requested by user_id: {user_id}, username: {username}")
    
    url = 'https://ecwonlive.com/en/home'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('div', {'id': 'v2cashfeed'}).find('table')
    rows = table.find('tbody').find_all('tr')[:9]
    
    withdrawals = []
    for row in rows:
        cols = row.find_all('td')
        player = cols[0].text.strip()
        withdraw = cols[3].text.strip()
        withdrawals.append(f"𝗨𝘀𝗲𝗿 𝗜𝗗: {player}\n𝗔𝗺𝗼𝘂𝗻𝘁: {withdraw}\n")
    
    now = datetime.now()
    date_str = now.strftime("%d/%m/%y")
    time_str = now.strftime("%H:%M")
    
    message = (
        "𝗖𝗼𝗻𝗴𝗿𝗮𝘁𝘂𝗹𝗮𝘁𝗶𝗼𝗻𝘀 𝘁𝗼 𝗮𝗹𝗹 𝗘𝗖𝗪𝗢𝗡 𝘄𝗶𝗻𝗻𝗲𝗿𝘀🎉\n"
        "Below is the live update of the last 9 winning transactions/withdrawals at 𝗘𝗖𝗪𝗢𝗡, updated as of "
        f"{date_str} - {time_str}\n\n" +
        "\n".join(withdrawals)
    )
    
    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(text="Play Now MY🇲🇾", url="https://t.me/ecwon8_bot/ec8my"),
        InlineKeyboardButton(text="Play Now Sg🇸🇬", url="https://t.me/ecwon8_bot/ec8sg")
    )
    inline_keyboard.add(InlineKeyboardButton(text="Back", callback_data="back"))
    
    gif_url = "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzdyNWRsdWQ0aTNycTc4ZTk3ZHBvNDB3eXZhOXI0bHM2c2RnMDZheSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/1lDFkU6NvBhsDRwSG4/giphy.gif"
    
    bot.send_animation(chat_id, gif_url, caption=message, reply_markup=inline_keyboard)