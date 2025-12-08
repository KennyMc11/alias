# game/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import GameRoom, Player

def index(request):
    """Главная страница игры"""
    return render(request, 'game/index.html')

def game_room(request, room_id):
    """Страница игровой комнаты"""
    room = get_object_or_404(GameRoom, room_id=room_id)
    players = room.players.all()
    
    context = {
        'room': room,
        'players': players,
        'team_a_players': players.filter(team='A'),
        'team_b_players': players.filter(team='B'),
    }
    return render(request, 'game/room.html', context)

@csrf_exempt
def api_create_room(request):
    """API для создания комнаты"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            username = data.get('username')
            difficulty = data.get('difficulty', 'medium')
            
            room = GameRoom.objects.create(
                creator_id=user_id,
                creator_name=username,
                difficulty=difficulty
            )
            
            # Создатель автоматически присоединяется к команде A
            Player.objects.create(
                room=room,
                user_id=user_id,
                username=username,
                team='A'
            )
            
            return JsonResponse({
                'success': True,
                'room_id': room.room_id,
                'message': 'Комната создана!'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_join_room(request):
    """API для присоединения к комнате"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room_id = data.get('room_id')
            user_id = data.get('user_id')
            username = data.get('username')
            team = data.get('team', 'A')
            
            room = get_object_or_404(GameRoom, room_id=room_id, is_active=True)
            
            # Проверяем, не присоединен ли уже пользователь
            if Player.objects.filter(room=room, user_id=user_id).exists():
                return JsonResponse({
                    'success': True,
                    'message': 'Вы уже в комнате',
                    'room_id': room.room_id
                })
            
            # Присоединяем пользователя
            Player.objects.create(
                room=room,
                user_id=user_id,
                username=username,
                team=team
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Вы присоединились к комнате',
                'room_id': room.room_id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_get_room_info(request, room_id):
    """Получить информацию о комнате"""
    room = get_object_or_404(GameRoom, room_id=room_id)
    players = list(room.players.values('user_id', 'username', 'team', 'score'))
    
    return JsonResponse({
        'room_id': room.room_id,
        'creator': room.creator_name,
        'difficulty': room.difficulty,
        'players': players,
        'team_a': [p for p in players if p['team'] == 'A'],
        'team_b': [p for p in players if p['team'] == 'B'],
    })

@csrf_exempt
def api_update_score(request):
    """Обновить счет игрока"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room_id = data.get('room_id')
            user_id = data.get('user_id')
            points = data.get('points', 0)
            
            player = get_object_or_404(Player, room__room_id=room_id, user_id=user_id)
            player.score += points
            player.save()
            
            return JsonResponse({
                'success': True,
                'new_score': player.score
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})