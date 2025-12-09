from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import GameRoom, Player
from .words import get_random_word

def index(request):
    return render(request, 'game/index.html')

def game_room(request, room_id):
    room = get_object_or_404(GameRoom, room_id=room_id)
    players = room.players.all()
    
    context = {
        'room': room,
        'players': players,
        'team_a_players': players.filter(team='A'),
        'team_b_players': players.filter(team='B'),
    }
    return render(request, 'game/room.html', context)

def game_play(request, room_id):
    room = get_object_or_404(GameRoom, room_id=room_id)
    return render(request, 'game/game.html', {'room': room})

@csrf_exempt
def api_create_room(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room = GameRoom.objects.create(
                creator_id=data['user_id'],
                creator_name=data['username'],
                difficulty=data.get('difficulty', 'medium')
            )
            return JsonResponse({'success': True, 'room_id': room.room_id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_join_room(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room = get_object_or_404(GameRoom, room_id=data['room_id'], is_active=True)
            return JsonResponse({'success': True, 'room_id': room.room_id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_join_team(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room = get_object_or_404(GameRoom, room_id=data['room_id'], is_active=True)
            
            Player.objects.filter(room=room, user_id=data['user_id']).delete()
            
            Player.objects.create(
                room=room,
                user_id=data['user_id'],
                username=data['username'],
                team=data['team']
            )
            
            return JsonResponse({'success': True, 'team': data['team']})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_get_room_info(request, room_id):
    try:
        room = GameRoom.objects.get(room_id=room_id)
        players = list(room.players.values('user_id', 'username', 'team', 'score'))
        
        return JsonResponse({
            'success': True,
            'room_id': room.room_id,
            'creator_name': room.creator_name,
            'difficulty': room.difficulty,
            'is_game_started': room.is_game_started,
            'players': players,
            'team_a': [p for p in players if p['team'] == 'A'],
            'team_b': [p for p in players if p['team'] == 'B'],
            'team_a_count': len([p for p in players if p['team'] == 'A']),
            'team_b_count': len([p for p in players if p['team'] == 'B']),
            'score_a': room.score_a,
            'score_b': room.score_b,
        })
    except GameRoom.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Комната не найдена'})

@csrf_exempt
def api_start_game(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room = get_object_or_404(GameRoom, room_id=data['room_id'])
            
            if room.creator_id != data['user_id']:
                return JsonResponse({'success': False, 'error': 'Только создатель может начать игру'})
            
            team_a_count = room.players.filter(team='A').count()
            team_b_count = room.players.filter(team='B').count()
            
            if team_a_count < 2 or team_b_count < 2:
                return JsonResponse({
                    'success': False,
                    'error': 'Нужно минимум по 2 игрока в каждой команде'
                })
            
            room.is_game_started = True
            room.save()
            
            return JsonResponse({'success': True, 'message': 'Игра началась!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_get_game_state(request, room_id):
    try:
        room = GameRoom.objects.get(room_id=room_id)
        
        if not room.is_game_started:
            return JsonResponse({'success': True, 'is_game_started': False})
        
        explainer, guesser = room.get_current_players()
        winner = None
        
        if room.score_a >= room.target_score:
            winner = 'A'
        elif room.score_b >= room.target_score:
            winner = 'B'
        
        return JsonResponse({
            'success': True,
            'is_game_started': True,
            'current_team': room.current_team,
            'score_a': room.score_a,
            'score_b': room.score_b,
            'target_score': room.target_score,
            'explainer': {
                'id': explainer.user_id if explainer else None,
                'username': explainer.username if explainer else None
            },
            'guesser': {
                'id': guesser.user_id if guesser else None,
                'username': guesser.username if guesser else None
            },
            'winner': winner,
            'time_per_turn': room.time_per_turn,
        })
    except GameRoom.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Комната не найдена'})

@csrf_exempt
def api_get_word(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room = GameRoom.objects.get(room_id=data['room_id'])
            
            explainer, _ = room.get_current_players()
            if not explainer or explainer.user_id != data['user_id']:
                return JsonResponse({'success': False, 'error': 'Не ваш ход'})
            
            used_words = json.loads(room.words_used)
            word = get_random_word(room.difficulty, used_words)
            
            if not word:
                used_words = []
                word = get_random_word(room.difficulty, used_words)
            
            used_words.append(word)
            room.words_used = json.dumps(used_words)
            room.save()
            
            return JsonResponse({'success': True, 'word': word})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_word_guessed(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room = GameRoom.objects.get(room_id=data['room_id'])
            
            explainer, _ = room.get_current_players()
            if not explainer or explainer.user_id != data['user_id']:
                return JsonResponse({'success': False, 'error': 'Не ваш ход'})
            
            if room.current_team == 'A':
                room.score_a += 1
            else:
                room.score_b += 1
            room.save()
            
            return JsonResponse({
                'success': True,
                'score_a': room.score_a,
                'score_b': room.score_b
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_next_turn(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room = GameRoom.objects.get(room_id=data['room_id'])
            
            explainer, _ = room.get_current_players()
            if room.creator_id != data['user_id'] and (not explainer or explainer.user_id != data['user_id']):
                return JsonResponse({'success': False, 'error': 'Недостаточно прав'})
            
            team_players = list(room.players.filter(team=room.current_team).order_by('id'))
            
            if len(team_players) < 2:
                return JsonResponse({'success': False, 'error': 'Недостаточно игроков'})
            
            room.current_explainer_index = room.current_guesser_index
            room.current_guesser_index = (room.current_guesser_index + 1) % len(team_players)
            
            if room.current_explainer_index == room.current_guesser_index:
                room.current_guesser_index = (room.current_guesser_index + 1) % len(team_players)
            
            room.save()
            
            return JsonResponse({
                'success': True,
                'current_team': room.current_team,
                'explainer_index': room.current_explainer_index,
                'guesser_index': room.current_guesser_index
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_switch_team(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room = GameRoom.objects.get(room_id=data['room_id'])
            
            if room.creator_id != data['user_id']:
                return JsonResponse({'success': False, 'error': 'Только создатель может сменить команду'})
            
            room.current_team = 'B' if room.current_team == 'A' else 'A'
            room.current_explainer_index = 0
            room.current_guesser_index = 1
            room.words_used = '[]'
            room.save()
            
            return JsonResponse({
                'success': True,
                'current_team': room.current_team,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_leave_room(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            Player.objects.filter(room__room_id=data['room_id'], user_id=data['user_id']).delete()
            
            room = GameRoom.objects.get(room_id=data['room_id'])
            if room.players.count() == 0:
                room.delete()
                return JsonResponse({'success': True, 'room_deleted': True})
            
            return JsonResponse({'success': True, 'room_deleted': False})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})