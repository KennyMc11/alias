# game/views.py
import json
import random
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import GameRoom, Player
from .words import get_random_word, get_all_words

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
    """Страница игрового процесса"""
    room = get_object_or_404(GameRoom, room_id=room_id)
    
    # Получаем user_id из Telegram Web App или GET параметров
    current_user_id = None
    
    # Пытаемся получить из Telegram Web App данных
    if request.GET.get('tg_data'):
        try:
            import json
            tg_data = json.loads(request.GET['tg_data'])
            current_user_id = tg_data.get('user', {}).get('id')
        except:
            pass
    
    # Если не получилось, используем дефолтное значение для теста
    if not current_user_id:
        current_user_id = request.GET.get('user_id', 0)
    
    context = {
        'room': room,
        'room_creator_id': room.creator_id,  # Передаем ID создателя
        'current_user_id': current_user_id,
    }
    return render(request, 'game/game.html', context)

@csrf_exempt
def api_create_room(request):
    if request.method == 'POST':
        try:
            print("Получен запрос на создание комнаты")
            print("Тело запроса:", request.body)
            
            data = json.loads(request.body)
            print("Данные:", data)
            
            user_id = data.get('user_id')
            username = data.get('username')
            difficulty = data.get('difficulty', 'medium')
            
            print(f"Создание комнаты: user_id={user_id}, username={username}, difficulty={difficulty}")
            
            if not user_id or not username:
                print("Ошибка: отсутствуют user_id или username")
                return JsonResponse({
                    'success': False,
                    'error': 'Отсутствуют данные пользователя'
                })
            
            room = GameRoom.objects.create(
                creator_id=user_id,
                creator_name=username,
                difficulty=difficulty
            )
            
            print(f"Комната создана: {room.room_id}")
            
            return JsonResponse({
                'success': True,
                'room_id': room.room_id,
            })
        except json.JSONDecodeError as e:
            print("Ошибка JSON:", e)
            return JsonResponse({'success': False, 'error': 'Неверный формат JSON'})
        except Exception as e:
            print("Общая ошибка:", e)
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_join_room(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room_id = data.get('room_id')
            user_id = data.get('user_id')
            username = data.get('username')
            
            room = get_object_or_404(GameRoom, room_id=room_id, is_active=True)
            
            if Player.objects.filter(room=room, user_id=user_id).exists():
                return JsonResponse({
                    'success': True,
                    'room_id': room.room_id
                })
            
            return JsonResponse({
                'success': True,
                'room_id': room.room_id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_join_team(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room_id = data.get('room_id')
            user_id = data.get('user_id')
            username = data.get('username')
            team = data.get('team', 'A')
            
            room = get_object_or_404(GameRoom, room_id=room_id, is_active=True)
            
            Player.objects.filter(room=room, user_id=user_id).delete()
            
            Player.objects.create(
                room=room,
                user_id=user_id,
                username=username,
                team=team
            )
            
            return JsonResponse({
                'success': True,
                'team': team
            })
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
            'difficulty': room.difficulty,
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
            room_id = data.get('room_id')
            user_id = data.get('user_id')
            
            room = get_object_or_404(GameRoom, room_id=room_id)
            
            if room.creator_id != user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Только создатель комнаты может начать игру'
                })
            
            team_a_count = room.players.filter(team='A').count()
            team_b_count = room.players.filter(team='B').count()
            
            if team_a_count < 2:
                return JsonResponse({
                    'success': False,
                    'error': 'В команде A должно быть минимум 2 игрока'
                })
            
            if team_b_count < 2:
                return JsonResponse({
                    'success': False,
                    'error': 'В команде B должно быть минимум 2 игрока'
                })
            
            room.is_game_started = True
            room.current_team = 'A'
            room.current_explainer_index = 0
            room.current_guesser_index = 1
            room.score_a = 0
            room.score_b = 0
            room.words_used = '[]'
            room.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Игра началась!'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_get_game_state(request, room_id):
    try:
        room = GameRoom.objects.get(room_id=room_id)
        
        if not room.is_game_started:
            return JsonResponse({
                'success': True,
                'is_game_started': False,
                'message': 'Игра еще не началась'
            })
        
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
                'username': explainer.username if explainer else 'Нет игрока'
            },
            'guesser': {
                'id': guesser.user_id if guesser else None,
                'username': guesser.username if guesser else 'Нет игрока'
            },
            'winner': winner,
            'time_per_turn': room.time_per_turn
        })
    except GameRoom.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Комната не найдена'})

@csrf_exempt
def api_get_word(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room_id = data.get('room_id')
            user_id = data.get('user_id')
            
            room = GameRoom.objects.get(room_id=room_id)
            
            explainer, _ = room.get_current_players()
            if not explainer or explainer.user_id != user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Сейчас не ваш ход для объяснения'
                })
            
            used_words = json.loads(room.words_used)
            word = get_random_word(room.difficulty, used_words)
            
            if not word:
                # Если все слова использованы, начинаем заново
                used_words = []
                word = get_random_word(room.difficulty, used_words)
            
            used_words.append(word)
            room.words_used = json.dumps(used_words)
            room.save()
            
            return JsonResponse({
                'success': True,
                'word': word
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_word_guessed(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room_id = data.get('room_id')
            user_id = data.get('user_id')
            
            room = GameRoom.objects.get(room_id=room_id)
            
            explainer, _ = room.get_current_players()
            if not explainer or explainer.user_id != user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Сейчас не ваш ход для объяснения'
                })
            
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
            room_id = data.get('room_id')
            user_id = data.get('user_id')
            
            room = GameRoom.objects.get(room_id=room_id)
            
            explainer, _ = room.get_current_players()
            if room.creator_id != user_id and (not explainer or explainer.user_id != user_id):
                return JsonResponse({
                    'success': False,
                    'error': 'Недостаточно прав'
                })
            
            team_players = list(room.players.filter(team=room.current_team).order_by('id'))
            
            if len(team_players) < 2:
                return JsonResponse({
                    'success': False,
                    'error': 'В команде должно быть минимум 2 игрока'
                })
            
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
            room_id = data.get('room_id')
            user_id = data.get('user_id')
            
            room = GameRoom.objects.get(room_id=room_id)
            
            if room.creator_id != user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Только создатель может сменить команду'
                })
            
            room.current_team = 'B' if room.current_team == 'A' else 'A'
            room.current_explainer_index = 0
            room.current_guesser_index = 1
            room.words_used = '[]'
            room.save()
            
            return JsonResponse({
                'success': True,
                'current_team': room.current_team,
                'message': f'Теперь играет команда {room.current_team}'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def api_leave_room(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            room_id = data.get('room_id')
            user_id = data.get('user_id')
            
            Player.objects.filter(room__room_id=room_id, user_id=user_id).delete()
            
            room = GameRoom.objects.get(room_id=room_id)
            if room.players.count() == 0:
                room.delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Комната удалена',
                    'room_deleted': True
                })
            
            return JsonResponse({
                'success': True,
                'message': 'Вы покинули комнату',
                'room_deleted': False
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})