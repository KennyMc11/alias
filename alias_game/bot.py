#!/usr/bin/env python
"""
Telegram Bot для игры Alias
"""

import os
import logging
import asyncio
from typing import Optional
from datetime import datetime

import telebot
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alias_game.settings')
django.setup()

from game.models import GameRoom, Player

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Получение токена
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
    exit(1)

# Создание бота
bot = AsyncTeleBot(TOKEN, state_storage=StateMemoryStorage())

class UserStates(StatesGroup):
    waiting_for_room_id = State()

@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """Обработка команды /start"""
    user = message.from_user
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

🎮 Добро пожаловать в игру Alias!

✨ Возможности:
• Создавайте игровые комнаты
• Приглашайте друзей
• Играйте в командах
• Объясняйте слова на время

📱 Чтобы начать игру, нажмите кнопку ниже:
"""
    
    # Создаем клавиатуру с Web App
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Основная кнопка для запуска игры
    web_app_info = types.WebAppInfo(url=f"{settings.ALLOWED_HOSTS[0]}/")
    keyboard.add(
        types.InlineKeyboardButton(
            text="🎮 Начать игру",
            web_app=web_app_info
        )
    )
    
    # Дополнительные кнопки
    keyboard.add(
        types.InlineKeyboardButton(
            text="📖 Правила игры",
            callback_data="rules"
        ),
        types.InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="stats"
        ),
        types.InlineKeyboardButton(
            text="👥 Мои комнаты",
            callback_data="my_rooms"
        )
    )
    
    await bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@bot.message_handler(commands=['play'])
async def play_command(message: types.Message):
    """Команда /play"""
    await send_welcome(message)

@bot.callback_query_handler(func=lambda call: call.data == "rules")
async def show_rules(call: types.CallbackQuery):
    """Показать правила игры"""
    rules_text = """
📖 <b>Правила игры Alias:</b>

🎯 <b>Цель игры:</b>
Первая команда, набравшая 25 очков, побеждает!

👥 <b>Состав команд:</b>
• Минимум 2 игрока в каждой команде
• Максимум 4 игрока в команде

🔄 <b>Ход игры:</b>
1. Команда А начинает игру
2. Игрок 1 объясняет слово Игроку 2
3. Если слово угадано → +1 очко команде
4. Если слово пропущено → следующее слово
5. Время на ход: 60 секунд
6. После хода игроки меняются ролями
7. Когда все игроки в команде объяснили, ход переходит другой команде

🚫 <b>Запрещено:</b>
• Использовать однокоренные слова
• Показывать жестами
• Использовать иностранные языки

✅ <b>Разрешено:</b>
• Описывать слово
• Использовать синонимы
• Объяснять по буквам (после 30 секунд)
"""
    
    await bot.answer_callback_query(call.id)
    await bot.send_message(
        call.message.chat.id,
        rules_text,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data == "stats")
async def show_stats(call: types.CallbackQuery):
    """Показать статистику"""
    user_id = call.from_user.id
    
    try:
        # Получаем статистику игрока
        total_games = GameRoom.objects.filter(players__user_id=user_id, is_game_started=True).count()
        total_wins = GameRoom.objects.filter(
            players__user_id=user_id,
            is_game_started=True
        ).filter(
            models.Q(score_a__gte=25) | models.Q(score_b__gte=25)
        ).count()
        
        # Получаем лучший счет
        player_stats = Player.objects.filter(user_id=user_id).aggregate(
            total_score=models.Sum('score'),
            avg_score=models.Avg('score'),
            max_score=models.Max('score')
        )
        
        stats_text = f"""
📊 <b>Ваша статистика:</b>

🎮 Сыграно игр: <b>{total_games}</b>
🏆 Побед: <b>{total_wins}</b>
📈 Процент побед: <b>{(total_wins/total_games*100) if total_games > 0 else 0:.1f}%</b>

🎯 Всего очков: <b>{player_stats['total_score'] or 0}</b>
⭐ Средний счет: <b>{player_stats['avg_score'] or 0:.1f}</b>
🚀 Лучший результат: <b>{player_stats['max_score'] or 0}</b>
"""
        
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            call.message.chat.id,
            stats_text,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await bot.answer_callback_query(call.id, "Ошибка при получении статистики")

@bot.callback_query_handler(func=lambda call: call.data == "my_rooms")
async def show_my_rooms(call: types.CallbackQuery):
    """Показать активные комнаты пользователя"""
    user_id = call.from_user.id
    
    try:
        # Получаем активные комнаты пользователя
        active_rooms = GameRoom.objects.filter(
            players__user_id=user_id,
            is_active=True
        ).order_by('-created_at')[:10]
        
        if active_rooms:
            rooms_text = "👥 <b>Ваши активные комнаты:</b>\n\n"
            
            for room in active_rooms:
                players_count = room.players.count()
                status = "🎮 Игра идет" if room.is_game_started else "⏳ Ожидание"
                
                rooms_text += f"""
🏠 <b>Комната {room.room_id}</b>
👤 Создатель: {room.creator_name}
👥 Игроков: {players_count}/8
🎯 Сложность: {room.get_difficulty_display()}
📊 Счет: {room.score_a}-{room.score_b}
🔄 Статус: {status}
🔗 Ссылка: {settings.ALLOWED_HOSTS[0]}/room/{room.room_id}/
"""
        else:
            rooms_text = "У вас нет активных комнат. Создайте новую!"
        
        keyboard = types.InlineKeyboardMarkup()
        web_app_info = types.WebAppInfo(url=f"{settings.ALLOWED_HOSTS[0]}/")
        keyboard.add(
            types.InlineKeyboardButton(
                text="🎮 Создать комнату",
                web_app=web_app_info
            )
        )
        
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            call.message.chat.id,
            rooms_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении комнат: {e}")
        await bot.answer_callback_query(call.id, "Ошибка при получении списка комнат")

@bot.message_handler(commands=['join'])
async def join_room_command(message: types.Message):
    """Команда для присоединения к комнате"""
    await bot.set_state(message.from_user.id, UserStates.waiting_for_room_id, message.chat.id)
    
    await bot.send_message(
        message.chat.id,
        "Введите ID комнаты для присоединения (6 символов):",
        reply_markup=types.ForceReply(selective=True)
    )

@bot.message_handler(state=UserStates.waiting_for_room_id)
async def process_room_id(message: types.Message):
    """Обработка введенного ID комнаты"""
    room_id = message.text.upper().strip()
    
    if len(room_id) != 6 or not room_id.isalnum():
        await bot.send_message(
            message.chat.id,
            "❌ Неверный формат ID комнаты. Должно быть 6 символов (буквы и цифры)."
        )
        return
    
    try:
        # Проверяем существование комнаты
        room = GameRoom.objects.get(room_id=room_id, is_active=True)
        
        # Создаем ссылку для присоединения
        join_url = f"{settings.ALLOWED_HOSTS[0]}/room/{room_id}/"
        
        keyboard = types.InlineKeyboardMarkup()
        web_app_info = types.WebAppInfo(url=join_url)
        keyboard.add(
            types.InlineKeyboardButton(
                text="🚪 Присоединиться к комнате",
                web_app=web_app_info
            )
        )
        
        await bot.send_message(
            message.chat.id,
            f"✅ Комната <b>{room_id}</b> найдена!\n"
            f"👤 Создатель: {room.creator_name}\n"
            f"🎯 Сложность: {room.get_difficulty_display()}\n"
            f"👥 Игроков: {room.players.count()}/8\n\n"
            f"Нажмите кнопку ниже, чтобы присоединиться:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        await bot.delete_state(message.from_user.id, message.chat.id)
        
    except GameRoom.DoesNotExist:
        await bot.send_message(
            message.chat.id,
            f"❌ Комната <b>{room_id}</b> не найдена или была удалена.",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка при поиске комнаты: {e}")
        await bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при поиске комнаты."
        )

@bot.message_handler(content_types=['web_app_data'])
async def handle_web_app_data(message: types.Message):
    """Обработка данных из Web App"""
    try:
        data = message.web_app_data.data
        logger.info(f"Получены данные из Web App: {data}")
        
        # Здесь можно обрабатывать данные, отправленные из Web App
        # Например, статистику, результаты игры и т.д.
        
        await bot.send_message(
            message.chat.id,
            "✅ Данные из игры получены!",
            reply_to_message_id=message.message_id
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки Web App данных: {e}")

@bot.message_handler(func=lambda message: True)
async def handle_all_messages(message: types.Message):
    """Обработка всех остальных сообщений"""
    if message.text:
        # Если сообщение похоже на ID комнаты
        if len(message.text) == 6 and message.text.isalnum():
            await join_room_command(message)
        else:
            await bot.send_message(
                message.chat.id,
                "Отправьте /start чтобы начать игру\n"
                "Или /join чтобы присоединиться к комнате"
            )

async def setup_webhook():
    """Настройка вебхука"""
    webhook_url = os.getenv('TELEGRAM_WEBHOOK_URL')
    if webhook_url:
        try:
            await bot.remove_webhook()
            await asyncio.sleep(1)
            await bot.set_webhook(
                url=webhook_url,
                certificate=open('/etc/nginx/ssl/fullchain.pem', 'r') if os.path.exists('/etc/nginx/ssl/fullchain.pem') else None,
                max_connections=100
            )
            logger.info(f"Webhook установлен: {webhook_url}")
        except Exception as e:
            logger.error(f"Ошибка установки webhook: {e}")

async def main():
    """Основная функция"""
    logger.info("Запуск бота Alias...")
    
    # Настраиваем вебхук если есть URL
    webhook_url = os.getenv('TELEGRAM_WEBHOOK_URL')
    if webhook_url:
        await setup_webhook()
        logger.info("Бот запущен в режиме webhook")
    else:
        logger.info("Бот запущен в режиме polling")
        await bot.infinity_polling()

if __name__ == '__main__':
    # Создаем директорию для логов
    os.makedirs('logs', exist_ok=True)
    
    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")