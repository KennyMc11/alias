import os
import sys

# Путь к корню проекта
project_home = '/home/Kenny11/alias/alias_game'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Путь к директории с настройками
settings_path = '/home/Kenny11/alias/alias_game/alias_game'
if settings_path not in sys.path:
    sys.path.insert(0, settings_path)

# Установите переменные окружения
os.environ['DJANGO_SETTINGS_MODULE'] = 'alias_game.settings'

# Загрузите Django приложение
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()