import os

# Структура проекта
tree = {
    "bot": {
        "handlers": {
            "__init__.py": "",
            "start.py": '''from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Это MalinaWB v2 (highload).\\n\\nГотов к работе!"
    )
''',
        },
        "keyboards": {
            "__init__.py": "",
        },
        "main.py": '''import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import start

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(
        start.router,
    )
    print("Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
'''
    },
    "services": {
        "wildberries_api.py": "# Тут будут асинхронные методы работы с Wildberries API\n",
        "report_generator.py": "# Тут будет генерация отчётов (Excel, PNG, PDF)\n",
        "celery_tasks.py": '''from celery import Celery

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
def example_task(x, y):
    return x + y
''',
    },
    "storage": {
        "redis_client.py": '''import redis

r = redis.Redis(host='localhost', port=6379, db=0)
''',
        "db.py": "# Тут будет подключение к БД (Postgres или SQLite)\n",
        "models.py": "# Тут будут модели пользователей и отчётов\n",
    },
    "templates": {},
    ".env.example": "BOT_TOKEN=ваш_токен_бота\n",
    "requirements.txt": '''aiogram==3.4.1
httpx
celery
redis
python-dotenv
asyncpg
''',
    "Dockerfile": '''FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "bot/main.py"]
''',
    "docker-compose.yml": '''version: "3"
services:
  bot:
    build: .
    env_file:
      - .env
    depends_on:
      - redis
      - celery_worker
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
  celery_worker:
    build: .
    command: celery -A services.celery_tasks worker --loglevel=info
    depends_on:
      - redis
''',
    "README.md": "# MalinaWBv2 Highload-ready Telegram Bot (aiogram + Celery + Redis)\n"
}

def create_tree(base, struct):
    for name, value in struct.items():
        path = os.path.join(base, name)
        if isinstance(value, dict):
            os.makedirs(path, exist_ok=True)
            create_tree(path, value)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(value)

create_tree(".", tree)
print("✅ Структура проекта создана! Теперь пропиши токен в .env и можешь работать.")
