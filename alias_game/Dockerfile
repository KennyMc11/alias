FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя
RUN useradd -m -u 1000 alias
USER alias
WORKDIR /app

# Копируем зависимости
COPY --chown=alias requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY --chown=alias . .

# Создаем директории
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Запуск
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "alias_game.wsgi:application"]