from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    # Пример простой админ-панели
    await message.answer(
        "👮‍♂️ Админ-панель. Здесь будут функции управления пользователями."
    )
# Здесь реализуй свои функции управления пользователями, подписками и др.
