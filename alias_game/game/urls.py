# game/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('room/<str:room_id>/', views.game_room, name='game_room'),
    path('api/create-room/', views.api_create_room, name='create_room'),
    path('api/join-room/', views.api_join_room, name='join_room'),
    path('api/room/<str:room_id>/', views.api_get_room_info, name='get_room_info'),
    path('api/update-score/', views.api_update_score, name='update_score'),
]