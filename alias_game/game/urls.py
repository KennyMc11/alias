# game/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('room/<str:room_id>/', views.game_room, name='game_room'),
    path('game/<str:room_id>/', views.game_play, name='game_play'),
    
    # API endpoints
    path('api/create-room/', views.api_create_room, name='create_room'),
    path('api/join-room/', views.api_join_room, name='join_room'),
    path('api/join-team/', views.api_join_team, name='join_team'),
    path('api/room/<str:room_id>/', views.api_get_room_info, name='get_room_info'),
    path('api/leave-room/', views.api_leave_room, name='leave_room'),
    
    # Game API
    path('api/start-game/', views.api_start_game, name='start_game'),
    path('api/game-state/<str:room_id>/', views.api_get_game_state, name='game_state'),
    path('api/get-word/', views.api_get_word, name='get_word'),
    path('api/word-guessed/', views.api_word_guessed, name='word_guessed'),
    path('api/next-turn/', views.api_next_turn, name='next_turn'),
    path('api/switch-team/', views.api_switch_team, name='switch_team'),
]