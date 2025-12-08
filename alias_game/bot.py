# bot.py
import telebot
from django.conf import settings
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alias_game.settings')
django.setup()

from game.models import GameRoom, Player

# Замените на ваш токен
TOKEN = 'ВАШ_TELEGRAM_BOT_TOKEN'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_command(message):
    # Создаем клавиатуру с одной кнопкой
    keyboard = telebot.types.InlineKeyboardMarkup()
    web_app = telebot.types.WebAppInfo(url="https://ваш-домен.com/")
    keyboard.add(telebot.types.InlineKeyboardButton(
        text="🎮 Играть", 
        web_app=web_app
    ))
    
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в игру Alias! Нажмите кнопку ниже, чтобы начать играть.",
        reply_markup=keyboard
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == '/play':
        start_command(message)
    else:
        bot.send_message(message.chat.id, "Нажмите /start чтобы начать игру")

# Web App обработчик
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    data = message.web_app_data.data
    # Здесь можно обрабатывать данные из Web App
    bot.send_message(message.chat.id, f"Получены данные: {data}")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)