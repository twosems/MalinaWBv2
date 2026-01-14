import asyncio
import logging
from os import getenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.bot_command import BotCommand
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from bot.handlers import start, reports, profile, admin, api_entry, main_menu
from bot.handlers import info
from bot.handlers import report_settings
from bot.reports import remains
from bot.reports.sales_by_articles import router as sales_by_articles_router
from bot.reports import sales_by_warehouses

from storage.db import engine, Base
from storage.users import daily_balance_update  # массовая актуализация баланса

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def async_db_init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def on_startup(bot: Bot):
    logger.info("Бот запущен!")


async def main():
    load_dotenv()
    BOT_TOKEN = getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан в .env!")

    # Инициализация БД (async)
    await async_db_init()

    # Инициализация бота и диспетчера
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров (важно: api_entry — первым)
    dp.include_router(api_entry.router)
    dp.include_router(start.router)
    dp.include_router(reports.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)
    dp.include_router(main_menu.router)
    dp.include_router(remains.router)
    dp.include_router(info.router)
    dp.include_router(sales_by_articles_router)
    dp.include_router(sales_by_warehouses.router)
    dp.include_router(report_settings.router)

    # Команды бота
    await bot.set_my_commands([
        BotCommand(command="start", description="Перезапуск/главное меню"),
        BotCommand(command="reports", description="Меню отчётов"),
        BotCommand(command="profile", description="Профиль"),
        BotCommand(command="admin", description="Админ-панель"),
    ])

    # Планировщик задач
    # Если нужна «полночь по Берлину», оставляем Europe/Berlin.
    # Если нужна именно UTC-полночь — поменять timezone на "UTC".
    scheduler = AsyncIOScheduler(timezone="Europe/Berlin")
    scheduler.add_job(daily_balance_update, "cron", hour=0, minute=0)  # ежедневно в 00:00
    scheduler.start()

    try:
        # В aiogram 3.x обычно регистрируют startup-хук иначе,
        # но если у тебя уже работает такой вызов — оставим.
        await dp.start_polling(bot, on_startup=on_startup)
    finally:
        # Сначала гасим планировщик, потом закрываем сессию бота
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
