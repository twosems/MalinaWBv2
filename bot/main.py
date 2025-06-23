"""
main.py — точка входа в Telegram-бота.
Запускает и инициализирует базу данных, настраивает роутеры и команды, стартует polling.

- Подключает все handlers через include_router.
- Инициализирует базу (create_all) через SQLAlchemy.
- Использует MemoryStorage для FSM (можно заменить на RedisStorage).
- Использует настройки из .env через dotenv.
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.bot_command import BotCommand
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties  # <-- добавлен импорт
from os import getenv
from dotenv import load_dotenv

from bot.handlers import start, reports, profile
# Добавь сюда свои дополнительные модули (например: admin, payments)

from storage.db import engine, Base

# 1. Асинхронная инициализация базы данных
async def async_db_init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def on_startup(bot: Bot):
    logging.info("Бот запущен!")

async def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    BOT_TOKEN = getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан в .env!")

    # 2. Инициализация базы данных
    await async_db_init()

    # 3. Инициализация бота и диспетчера
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 4. Подключение роутеров
    dp.include_router(start.router)
    dp.include_router(reports.router)
    dp.include_router(profile.router)
    # Здесь добавляй другие роутеры (admin, payments и т.д.)

    # 5. Команды меню
    await bot.set_my_commands([
        BotCommand(command="start", description="Перезапуск/главное меню"),
        BotCommand(command="reports", description="Меню отчётов"),
        BotCommand(command="profile", description="Профиль"),
    ])

    # 6. Запуск бота
    await dp.start_polling(bot, on_startup=on_startup)

if __name__ == "__main__":
    asyncio.run(main())
