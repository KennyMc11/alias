#!/usr/bin/env python
"""
Тестирование полного цикла игры
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alias_game.settings')
django.setup()

from game.models import GameRoom, Player
from game.words import get_random_word

print("=== Тестирование игры Alias ===")

# 1. Создаем тестовую комнату
print("\n1. Создание комнаты...")
room = GameRoom.objects.create(
    creator_id=123456789,
    creator_name="Тестовый Создатель",
    difficulty="easy"
)
print(f"   Комната создана: {room.room_id}")

# 2. Добавляем игроков
print("\n2. Добавление игроков...")
players_data = [
    (111111111, "Игрок1", "A"),
    (222222222, "Игрок2", "A"),
    (333333333, "Игрок3", "B"),
    (444444444, "Игрок4", "B"),
]

for user_id, username, team in players_data:
    Player.objects.create(
        room=room,
        user_id=user_id,
        username=username,
        team=team
    )
    print(f"   Добавлен: {username} в команду {team}")

# 3. Начинаем игру
print("\n3. Начало игры...")
room.is_game_started = True
room.save()
print("   Игра начата!")

# 4. Тестируем получение слов
print("\n4. Тестирование слов...")
for i in range(5):
    word = get_random_word(room.difficulty, [])
    print(f"   Слово {i+1}: {word}")

# 5. Проверяем состояние комнаты
print("\n5. Состояние комнаты:")
print(f"   ID: {room.room_id}")
print(f"   Создатель: {room.creator_name}")
print(f"   Сложность: {room.difficulty}")
print(f"   Игра идет: {room.is_game_started}")
print(f"   Счет A: {room.score_a}, B: {room.score_b}")
print(f"   Цель: {room.target_score} слов")

# 6. Проверяем игроков
print("\n6. Список игроков:")
for player in room.players.all():
    print(f"   • {player.username} (команда {player.team})")

print("\n=== Тест завершен успешно! ===")
