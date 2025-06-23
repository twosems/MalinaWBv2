from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from storage.users import set_api_key  # реализация — в models.py/users.py

router = Router()

@router.message(F.text.regexp(r"^/api\s+[\w\-]+"))
async def set_api(message: Message):
    # Пример: пользователь вводит /api <ключ>
    user_id = message.from_user.id
    api_key = message.text.split(maxsplit=1)[1]
    await set_api_key(user_id, api_key)
    await message.answer("API-ключ сохранён!")

@router.callback_query(F.data == "api_change")
async def api_change(callback: CallbackQuery):
    await callback.message.answer("Пришли мне новый API-ключ в формате:\n<code>/api ТВОЙ_КЛЮЧ</code>", parse_mode="HTML")
    await callback.answer()
