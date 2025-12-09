from django.contrib import admin
from .models import GameRoom, Player

@admin.register(GameRoom)
class GameRoomAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'creator_name', 'difficulty', 'is_active', 'is_game_started', 'created_at')
    list_filter = ('is_active', 'is_game_started', 'difficulty')
    search_fields = ('room_id', 'creator_name')

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('username', 'room', 'team', 'score', 'joined_at')
    list_filter = ('team',)
    search_fields = ('username', 'room__room_id')