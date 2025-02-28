import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, config, bot_owner_id, bot_admin_ids
from datetime import datetime
import pytz

GIPHY_API_KEY = 'oTvmjx3ZqxwK1daHDc3ZSYjIdKBr8EMg'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    with open(CONFIG_FILE, 'r') as file:
        return json.load(file)

config = load_config()

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)
        
def send_sport_arena_post(chat_id):
    gif_url = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExMXRjeXF6NnYwc2hhdWlza2pvYjNwdnRvdmZkOHBtcDM5MG54aHFldyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/US19GAfqs4E55kGqYD/giphy.gif"
    
    inline_keyboard = InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(text="⚽️UEFA Euro", callback_data="get_europe"),
        InlineKeyboardButton(text="⚽️Premier League", callback_data="get_premier_league"),
        InlineKeyboardButton(text="⚽️Bundesliga", callback_data="get_bundesliga"),
        InlineKeyboardButton(text="⚽️Serie A", callback_data="get_serie_a"),
        InlineKeyboardButton(text="⚽️La Liga", callback_data="get_la_liga"),
        InlineKeyboardButton(text="⚽️FIFA Worldcup", callback_data="get_worldcup"),
        InlineKeyboardButton(text="⚽️Champions League", callback_data="get_champions_league")
    )
    inline_keyboard.add(InlineKeyboardButton(text="Back", callback_data="back"))

    caption = (
        "⚽ Choose Your Favorite League, Get Live Match Results, Updated Schedules, and the Best Odds Just for You!\n"
        "Stay Ahead of the Game! ⏰🔥"
    )
    
    bot.send_animation(chat_id, gif_url, caption=caption, reply_markup=inline_keyboard)
    logging.info(f"send_sport_arena_post called by user_id: {chat_id}")

def add_bet_buttons(inline_keyboard, config, user_id):
    button_bet = config['button_bet']
    inline_keyboard.add(
        InlineKeyboardButton(text=button_bet['place_bet_my']['text'], url=button_bet['place_bet_my']['url'])
    )
    inline_keyboard.add(    
        InlineKeyboardButton(text=button_bet['place_bet_sg']['text'], url=button_bet['place_bet_sg']['url'])
    )
    
    # Check if the user is an admin or owner
    if user_id == bot_owner_id or user_id in bot_admin_ids:
        inline_keyboard.add(
            InlineKeyboardButton(text="⚙️Settings Button⚙️", callback_data="settingplace_button")
        )
    
    inline_keyboard.add(
        InlineKeyboardButton(text="Back", callback_data="back")
    )
    
#Champions League
@bot.callback_query_handler(func=lambda call: call.data == "get_champions_league")
def champions_league_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_champions_league' button")

    # Fetch a random GIF with the hashtag "champions league" from Giphy
    giphy_url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag=champions+league"
    response = requests.get(giphy_url)
    data = response.json()
    gif_url = data['data']['images']['original']['url']

    # Create inline buttons
    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(text="⬅️Recent Matches", callback_data="get_clrecent_matches"),
        InlineKeyboardButton(text="Next Matches➡️", callback_data="get_clnext_matches")
    )
    add_bet_buttons(inline_keyboard, config, user_id)

    # Send the random GIF with inline buttons
    bot.send_animation(chat_id, gif_url, reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "get_clrecent_matches")
def recent_clmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/CL/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    logging.info(f"User {username} (ID: {user_id}) pressed 'get_clrecent_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='last_matches')
    matches = matches_table.find_all('tr')

    message = f"📈𝗥𝗲𝘀𝘂𝗹𝘁𝘀 𝗢𝗳 𝗧𝗵𝗲 𝗟𝗮𝘀𝘁 𝟭𝟬 𝗠𝗮𝘁𝗰𝗵𝗲𝘀📉\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        score = match.find('td', class_='whitespace-nowrap').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        home_odds, draw_odds, away_odds = odds

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"Results : {score.replace(':', ' - ')}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)   

@bot.callback_query_handler(func=lambda call: call.data == "get_clnext_matches")
def next_clmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/CL/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_clnext_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='next_matches')
    matches = matches_table.find_all('tr')

    message = f"🗓𝟭𝟬 𝗨𝗽𝗰𝗼𝗺𝗶𝗻𝗴 𝗠𝗮𝘁𝗰𝗵 𝗦𝗰𝗵𝗲𝗱𝘂𝗹𝗲🗓\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text.strip()
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        
        if len(odds) == 3:
            home_odds, draw_odds, away_odds = odds
        else:
            home_odds, draw_odds, away_odds = "-", "-", "-"

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)  

#Premier League
@bot.callback_query_handler(func=lambda call: call.data == "get_premier_league")
def premier_league_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_premier_league' button")

    giphy_url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag=premier+league"
    response = requests.get(giphy_url)
    data = response.json()
    gif_url = data['data']['images']['original']['url']

    # Create inline buttons
    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(text="⬅️Recent Matches", callback_data="get_plrecent_matches"),
        InlineKeyboardButton(text="Next Matches➡️", callback_data="get_plnext_matches")
    )
    add_bet_buttons(inline_keyboard, config, user_id)

    # Send the random GIF with inline buttons
    bot.send_animation(chat_id, gif_url, reply_markup=inline_keyboard)  

@bot.callback_query_handler(func=lambda call: call.data == "get_plrecent_matches")
def recent_plmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/PL/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_plrecent_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='last_matches')
    matches = matches_table.find_all('tr')

    message = f"📈𝗥𝗲𝘀𝘂𝗹𝘁𝘀 𝗢𝗳 𝗧𝗵𝗲 𝗟𝗮𝘀𝘁 𝟭𝟬 𝗠𝗮𝘁𝗰𝗵𝗲𝘀📉\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        score = match.find('td', class_='whitespace-nowrap').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        home_odds, draw_odds, away_odds = odds

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"Results : {score.replace(':', ' - ')}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "get_plnext_matches")
def next_plmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/PL/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_plnext_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='next_matches')
    matches = matches_table.find_all('tr')

    message = f"🗓𝟭𝟬 𝗨𝗽𝗰𝗼𝗺𝗶𝗻𝗴 𝗠𝗮𝘁𝗰𝗵 𝗦𝗰𝗵𝗲𝗱𝘂𝗹𝗲🗓\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text.strip()
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        
        if len(odds) == 3:
            home_odds, draw_odds, away_odds = odds
        else:
            home_odds, draw_odds, away_odds = "-", "-", "-"

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)    

#Bundesliga
@bot.callback_query_handler(func=lambda call: call.data == "get_bundesliga")
def bundes_league_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_bundesliga' button")

    # Fetch a random GIF with the hashtag "champions league" from Giphy
    giphy_url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag=bundes+league"
    response = requests.get(giphy_url)
    data = response.json()
    gif_url = data['data']['images']['original']['url']

    # Create inline buttons
    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(text="⬅️Recent Matches", callback_data="get_blrecent_matches"),
        InlineKeyboardButton(text="Next Matches➡️", callback_data="get_blnext_matches")
    )
    add_bet_buttons(inline_keyboard, config, user_id)

    # Send the random GIF with inline buttons
    bot.send_animation(chat_id, gif_url, reply_markup=inline_keyboard)    

@bot.callback_query_handler(func=lambda call: call.data == "get_blrecent_matches")
def recent_blmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/BL1/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_blrecent_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='last_matches')
    matches = matches_table.find_all('tr')

    message = f"📈𝗥𝗲𝘀𝘂𝗹𝘁𝘀 𝗢𝗳 𝗧𝗵𝗲 𝗟𝗮𝘀𝘁 𝟭𝟬 𝗠𝗮𝘁𝗰𝗵𝗲𝘀📉\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        score = match.find('td', class_='whitespace-nowrap').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        home_odds, draw_odds, away_odds = odds

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"Results : {score.replace(':', ' - ')}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "get_blnext_matches")
def next_blmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/BL1/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_blnext_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='next_matches')
    matches = matches_table.find_all('tr')

    message = f"🗓𝟭𝟬 𝗨𝗽𝗰𝗼𝗺𝗶𝗻𝗴 𝗠𝗮𝘁𝗰𝗵 𝗦𝗰𝗵𝗲𝗱𝘂𝗹𝗲🗓\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text.strip()
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        
        if len(odds) == 3:
            home_odds, draw_odds, away_odds = odds
        else:
            home_odds, draw_odds, away_odds = "-", "-", "-"

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)   

#SERIE A
@bot.callback_query_handler(func=lambda call: call.data == "get_serie_a")
def serie_a_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_serie_a' button")

    # Fetch a random GIF with the hashtag "champions league" from Giphy
    giphy_url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag=serie+a"
    response = requests.get(giphy_url)
    data = response.json()
    gif_url = data['data']['images']['original']['url']

    # Create inline buttons
    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(text="⬅️Recent Matches", callback_data="get_sarecent_matches"),
        InlineKeyboardButton(text="Next Matches➡️", callback_data="get_sanext_matches")
    )
    add_bet_buttons(inline_keyboard, config, user_id)

    # Send the random GIF with inline buttons
    bot.send_animation(chat_id, gif_url, reply_markup=inline_keyboard)    

@bot.callback_query_handler(func=lambda call: call.data == "get_sarecent_matches")
def recent_samatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/SA/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_sarecent_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='last_matches')
    matches = matches_table.find_all('tr')

    message = f"📈𝗥𝗲𝘀𝘂𝗹𝘁𝘀 𝗢𝗳 𝗧𝗵𝗲 𝗟𝗮𝘀𝘁 𝟭𝟬 𝗠𝗮𝘁𝗰𝗵𝗲𝘀📉\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        score = match.find('td', class_='whitespace-nowrap').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        home_odds, draw_odds, away_odds = odds

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"Results : {score.replace(':', ' - ')}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "get_sanext_matches")
def next_samatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/SA/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_sanext_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='next_matches')
    matches = matches_table.find_all('tr')

    message = f"🗓𝟭𝟬 𝗨𝗽𝗰𝗼𝗺𝗶𝗻𝗴 𝗠𝗮𝘁𝗰𝗵 𝗦𝗰𝗵𝗲𝗱𝘂𝗹𝗲🗓\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text.strip()
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        
        if len(odds) == 3:
            home_odds, draw_odds, away_odds = odds
        else:
            home_odds, draw_odds, away_odds = "-", "-", "-"

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)   

#La Liga
@bot.callback_query_handler(func=lambda call: call.data == "get_la_liga")
def la_liga_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_la_liga' button")

    # Fetch a random GIF with the hashtag "champions league" from Giphy
    giphy_url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag=la+liga"
    response = requests.get(giphy_url)
    data = response.json()
    gif_url = data['data']['images']['original']['url']

    # Create inline buttons
    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(text="⬅️Recent Matches", callback_data="get_pdrecent_matches"),
        InlineKeyboardButton(text="Next Matches➡️", callback_data="get_pdnext_matches")
    )
    add_bet_buttons(inline_keyboard, config, user_id)

    # Send the random GIF with inline buttons
    bot.send_animation(chat_id, gif_url, reply_markup=inline_keyboard)    

@bot.callback_query_handler(func=lambda call: call.data == "get_pdrecent_matches")
def recent_pdmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/PD/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_pdrecent_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='last_matches')
    matches = matches_table.find_all('tr')

    message = f"📈𝗥𝗲𝘀𝘂𝗹𝘁𝘀 𝗢𝗳 𝗧𝗵𝗲 𝗟𝗮𝘀𝘁 𝟭𝟬 𝗠𝗮𝘁𝗰𝗵𝗲𝘀📉\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        score = match.find('td', class_='whitespace-nowrap').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        home_odds, draw_odds, away_odds = odds

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"Results : {score.replace(':', ' - ')}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "get_pdnext_matches")
def next_pdmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/PD/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_pdnext_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='next_matches')
    matches = matches_table.find_all('tr')

    message = f"🗓𝟭𝟬 𝗨𝗽𝗰𝗼𝗺𝗶𝗻𝗴 𝗠𝗮𝘁𝗰𝗵 𝗦𝗰𝗵𝗲𝗱𝘂𝗹𝗲🗓\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text.strip()
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        
        if len(odds) == 3:
            home_odds, draw_odds, away_odds = odds
        else:
            home_odds, draw_odds, away_odds = "-", "-", "-"

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)   

#World Cup
@bot.callback_query_handler(func=lambda call: call.data == "get_worldcup")
def worldcup_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_worldcup' button")

    # Fetch a random GIF with the hashtag "champions league" from Giphy
    giphy_url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag=world+cup"
    response = requests.get(giphy_url)
    data = response.json()
    gif_url = data['data']['images']['original']['url']

    # Create inline buttons
    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(text="⬅️Recent Matches", callback_data="get_wcrecent_matches"),
        InlineKeyboardButton(text="Next Matches➡️", callback_data="get_wcnext_matches")
    )
    add_bet_buttons(inline_keyboard, config, user_id)

    # Send the random GIF with inline buttons
    bot.send_animation(chat_id, gif_url, reply_markup=inline_keyboard)    

@bot.callback_query_handler(func=lambda call: call.data == "get_wcrecent_matches")
def recent_wcmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/WC/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_wcrecent_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='last_matches')
    matches = matches_table.find_all('tr')

    message = f"📈𝗥𝗲𝘀𝘂𝗹𝘁𝘀 𝗢𝗳 𝗧𝗵𝗲 𝗟𝗮𝘀𝘁 𝟭𝟬 𝗠𝗮𝘁𝗰𝗵𝗲𝘀📉\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text.strip()
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        score = match.find('td', class_='whitespace-nowrap').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        
        if len(odds) == 3:
            home_odds, draw_odds, away_odds = odds
        else:
            home_odds, draw_odds, away_odds = "-", "-", "-"

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"Results : {score.replace(':', ' - ')}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "get_wcnext_matches")
def next_wcmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/WC/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_wcnext_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='next_matches')
    matches = matches_table.find_all('tr')

    message = f"🗓𝟭𝟬 𝗨𝗽𝗰𝗼𝗺𝗶𝗻𝗴 𝗠𝗮𝘁𝗰𝗵 𝗦𝗰𝗵𝗲𝗱𝘂𝗹𝗲🗓\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text.strip()
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        
        if len(odds) == 3:
            home_odds, draw_odds, away_odds = odds
        else:
            home_odds, draw_odds, away_odds = "-", "-", "-"

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)       

#UEFA EUROPE
@bot.callback_query_handler(func=lambda call: call.data == "get_europe")
def worldcup_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_europe' button")

    giphy_url = f"https://api.giphy.com/v1/gifs/random?api_key={GIPHY_API_KEY}&tag=euro+cup"
    response = requests.get(giphy_url)
    data = response.json()
    gif_url = data['data']['images']['original']['url']

    # Create inline buttons
    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
    inline_keyboard.add(
        InlineKeyboardButton(text="⬅️Recent Matches", callback_data="get_ecrecent_matches"),
        InlineKeyboardButton(text="Next Matches➡️", callback_data="get_ecnext_matches")
    )
    add_bet_buttons(inline_keyboard, config, user_id)

    # Send the random GIF with inline buttons
    bot.send_animation(chat_id, gif_url, reply_markup=inline_keyboard)    

@bot.callback_query_handler(func=lambda call: call.data == "get_ecrecent_matches")
def recent_ecmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/EC/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_ecrecent_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='last_matches')
    matches = matches_table.find_all('tr')

    message = f"📈𝗥𝗲𝘀𝘂𝗹𝘁𝘀 𝗢𝗳 𝗧𝗵𝗲 𝗟𝗮𝘀𝘁 𝟭𝟬 𝗠𝗮𝘁𝗰𝗵𝗲𝘀📉\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text.strip()
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        score = match.find('td', class_='whitespace-nowrap').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        
        if len(odds) == 3:
            home_odds, draw_odds, away_odds = odds
        else:
            home_odds, draw_odds, away_odds = "-", "-", "-"

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"Results : {score.replace(':', ' - ')}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "get_ecnext_matches")
def next_ecmatches_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username
    url = "https://native-stats.org/competition/EC/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    logging.info(f"User {username} (ID: {user_id}) pressed 'get_ecnext_matches' button")

    league_info = soup.find('div', class_='ml-2')
    league_name = league_info.find('h4').text.strip()
    season = league_info.find('p').text.strip()

    matches_table = soup.find('tbody', id='next_matches')
    matches = matches_table.find_all('tr')

    message = f"🗓𝟭𝟬 𝗨𝗽𝗰𝗼𝗺𝗶𝗻𝗴 𝗠𝗮𝘁𝗰𝗵 𝗦𝗰𝗵𝗲𝗱𝘂𝗹𝗲🗓\n\n⚽️{league_name}\n🏆{season}\n\n"
    for match in matches:
        date_str = match.find('th').text.strip()
        date_obj = datetime.strptime(date_str, "%Y/%m/%d, %Hh%M")
        cet_tz = pytz.timezone('CET')
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        date_obj = cet_tz.localize(date_obj).astimezone(malaysia_tz)
        date = date_obj.strftime("%d/%m/%Y, %H:%M")

        teams = match.find_all('div', class_='content')
        team1 = teams[0].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        team2 = teams[1].find('span', class_='hidden text-gray-200 align-middle md:inline-block').text.strip()
        odds = match.find_all('td', class_='whitespace-nowrap')[1].text.strip().split(' / ')
        
        if len(odds) == 3:
            home_odds, draw_odds, away_odds = odds
        else:
            home_odds, draw_odds, away_odds = "-", "-", "-"

        message += (
            f"Date & Time : {date}\n"
            f"{team1} 🆚 {team2}\n"
            f"🔸Odds🔸\n"
            f"Home : {home_odds}\n"
            f"Draw : {draw_odds}\n"
            f"Away : {away_odds}\n\n"
        )

    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, message, reply_markup=inline_keyboard)


#Fungsi Setting
@bot.callback_query_handler(func=lambda call: call.data == "settingplace_button")
def settings_button_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    # Create inline buttons for changing button name and link
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        InlineKeyboardButton(text="Change Button Name", callback_data="change_place_button_name"),
        InlineKeyboardButton(text="Change Button Link", callback_data="change_place_button_link")
    )
    inline_keyboard.add(InlineKeyboardButton(text="Back", callback_data="back"))

    bot.send_message(chat_id, "Settings Menu:", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "change_place_button_name")
def handle_change_place_button_name(call):
    chat_id = call.message.chat.id
    config = load_config()
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        types.InlineKeyboardButton(text=config['button_bet']['place_bet_my']['text'], callback_data="change_place_name_place_bet_my"),
        types.InlineKeyboardButton(text=config['button_bet']['place_bet_sg']['text'], callback_data="change_place_name_place_bet_sg")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Back", callback_data="back")
    )
    bot.send_message(chat_id, "Which button name do you want to change?", reply_markup=inline_keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "change_place_button_link")
def handle_change_place_button_link(call):
    chat_id = call.message.chat.id
    config = load_config()
    inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
    inline_keyboard.add(
        types.InlineKeyboardButton(text=config['button_bet']['place_bet_my']['text'], callback_data="change_place_link_place_bet_my"),
        types.InlineKeyboardButton(text=config['button_bet']['place_bet_sg']['text'], callback_data="change_place_link_place_bet_sg")
    )
    inline_keyboard.add(
        types.InlineKeyboardButton(text="Back", callback_data="back")
    )
    bot.send_message(chat_id, "Which button link do you want to change?", reply_markup=inline_keyboard)

def update_button_place_name(bot, chat_id, button_key, new_name):
    global config
    config = load_config()
    config['button_bet'][button_key]['text'] = new_name
    save_config(config)
    bot.send_message(chat_id, f"Button name updated to: {new_name}")
    config = load_config()
    send_sport_arena_post(chat_id)

def update_button_place_link(bot, chat_id, button_key, new_link):
    global config
    config = load_config()
    config['button_bet'][button_key]['url'] = new_link
    save_config(config)
    bot.send_message(chat_id, f"Button link updated to: {new_link}")
    config = load_config()
    send_sport_arena_post(chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_place_name_"))
def callback_update_button_place_name(call):
    button_key = call.data.replace("change_place_name_", "")
    msg = bot.send_message(call.message.chat.id, "Please enter the new button name:")
    bot.register_next_step_handler(msg, lambda message: update_button_place_name(bot, call.message.chat.id, button_key, message.text))

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_place_link_"))
def callback_update_button_place_link(call):
    button_key = call.data.replace("change_place_link_", "")
    msg = bot.send_message(call.message.chat.id, "Please enter the new button link:")
    bot.register_next_step_handler(msg, lambda message: update_button_place_link(bot, call.message.chat.id, button_key, message.text))