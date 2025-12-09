from django.db import models
import string
import random
import json

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
    is_game_started = models.BooleanField(default=False)
    current_round = models.IntegerField(default=1)
    current_team = models.CharField(max_length=1, choices=[('A', 'Команда A'), ('B', 'Команда B')], default='A')
    current_explainer_index = models.IntegerField(default=0)
    current_guesser_index = models.IntegerField(default=1)
    words_used = models.TextField(default='[]')
    score_a = models.IntegerField(default=0)
    score_b = models.IntegerField(default=0)
    target_score = models.IntegerField(default=25)
    time_per_turn = models.IntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Комната {self.room_id}"
    
    def get_current_players(self):
        team_players = list(self.players.filter(team=self.current_team).order_by('id'))
        
        if not team_players:
            return None, None
        
        explainer_index = self.current_explainer_index % len(team_players)
        guesser_index = self.current_guesser_index % len(team_players)
        
        if explainer_index == guesser_index:
            guesser_index = (guesser_index + 1) % len(team_players)
        
        explainer = team_players[explainer_index] if team_players else None
        guesser = team_players[guesser_index] if team_players else None
        
        return explainer, guesser

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