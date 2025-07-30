import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.bot_command import BotCommand
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from os import getenv
from dotenv import load_dotenv
from bot.handlers import start, reports, profile, admin, api_entry, main_menu
from storage.db import engine, Base
from bot.reports import remains
from bot.handlers import info
from bot.reports.sales_by_articles import router as sales_by_articles_router
from bot.reports import sales_by_warehouses
#from bot.handlers.reports import router as reports_router
from aiogram import Dispatcher
from bot.handlers import report_settings

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

    await async_db_init()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем все роутеры
    dp.include_router(api_entry.router)  # Должен быть ПЕРВЫМ!
    dp.include_router(start.router)
    dp.include_router(reports.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)
    dp.include_router(main_menu.router)
    dp.include_router(remains.router)
    dp.include_router(info.router)
    #dp.include_router(sales_router)
    dp.include_router(sales_by_articles_router)
    dp.include_router(sales_by_warehouses.router)
    dp.include_router(report_settings.router)


    # Меню команд для Telegram
    await bot.set_my_commands([
        BotCommand(command="start", description="Перезапуск/главное меню"),
        BotCommand(command="reports", description="Меню отчётов"),
        BotCommand(command="profile", description="Профиль"),
        BotCommand(command="admin", description="Админ-панель"),
    ])

    await dp.start_polling(bot, on_startup=on_startup)

if __name__ == "__main__":
    asyncio.run(main())
