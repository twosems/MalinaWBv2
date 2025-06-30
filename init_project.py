from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio
import logging

API_TOKEN = '7971708913:AAG6QBNsT2_iYPbewXBd7YQ99IsiZ6pcclU'

# Включаем логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("myid"))
async def get_my_id(message: types.Message):
    # Получаем user_id и логируем
    user_id = message.from_user.id
    logging.info(f"[DEBUG TEST] user_id from message: {user_id}")
    await message.answer(f"Твой user_id: <code>{user_id}</code>", parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
