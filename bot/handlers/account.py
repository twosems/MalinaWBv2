from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from storage.users import get_user_access

router = Router()

def profile_inline_keyboard():
    kb = [
        [InlineKeyboardButton("💳 Пополнить баланс", callback_data="buy")],
        [InlineKeyboardButton("⬅️ В меню", callback_data="account_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(F.text == "👤 Профиль")
async def profile_menu(message: Message):
    user_id = message.from_user.id
    access = await get_user_access(user_id)
    now = datetime.now()

    if access and access.paid_until and access.paid_until > now:
        status = f"Баланс: <b>доступ до {access.paid_until.strftime('%d.%m.%Y %H:%M')}</b>"
    elif access and access.trial_activated and access.trial_until and access.trial_until > now:
        status = f"Пробный доступ до {access.trial_until.strftime('%H:%M')}"
    else:
        status = "Нет активной подписки."

    text = (
        f"👤 <b>Профиль</b>\n"
        f"{status}\n\n"
        "<i>Здесь вы можете управлять подпиской и API-ключом.</i>"
    )
    await message.answer(text, reply_markup=profile_inline_keyboard(), parse_mode="HTML")
