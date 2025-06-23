from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

router = Router()

@router.callback_query(F.data == "buy")
async def buy_access(callback: CallbackQuery):
    await callback.message.edit_text(
        "💳 Оплата пока не реализована.\n"
        "Попросите администратора выдать доступ вручную."
    )
    await callback.answer()
