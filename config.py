"""
config.py — загрузка и хранение основных параметров конфигурации проекта.

Структура и принцип работы:
- Загружает переменные среды из файла .env с помощью dotenv.
- BOT_TOKEN: Telegram Bot API Token (для запуска и авторизации бота).
- POSTGRES_DSN: строка подключения к базе данных PostgreSQL (используется SQLAlchemy).
- Можно добавить дополнительные параметры (например, REDIS_DSN), если потребуется.

Все параметры доступны из других частей проекта через импорт этого файла.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env

BOT_TOKEN = os.getenv("BOT_TOKEN")
POSTGRES_DSN = os.getenv("POSTGRES_DSN")
ADMINS = [699875303]  # сюда твой Telegram user_id, и других админов, если есть
