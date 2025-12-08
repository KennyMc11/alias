# game/models.py
from django.db import models
import string
import random

def generate_room_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class GameRoom(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Легкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ]
    
    room_id = models.CharField(max_length=6, default=generate_room_id, unique=True)
    creator_id = models.BigIntegerField()
    creator_name = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Комната {self.room_id}"

class Player(models.Model):
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='players')
    user_id = models.BigIntegerField()
    username = models.CharField(max_length=100)
    team = models.CharField(max_length=1, choices=[('A', 'Команда A'), ('B', 'Команда B')])
    score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['room', 'user_id']
    
    def __str__(self):
        return f"{self.username} в комнате {self.room.room_id}"