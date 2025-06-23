# bot/handlers/start.py

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta

from storage.users import (
    get_user_access,
    create_user_access,
    set_trial_access
)

router = Router()

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Отчёты")],
            [KeyboardButton(text="👤 Профиль")],
        ],
        resize_keyboard=True
    )

def access_keyboard(trial_active, trial_expired):
    kb = []
    if not trial_active and not trial_expired:
        kb.append([InlineKeyboardButton(text="🕒 Пробный доступ (1 час)", callback_data="trial")])
    else:
        label = "🕒 Пробный доступ (уже активирован)" if trial_expired else "🕒 Пробный доступ (активен)"
        kb.append([InlineKeyboardButton(text=label, callback_data="trial_disabled")])
    kb.append([InlineKeyboardButton(text="💳 Оплатить доступ 399₽/мес", callback_data="buy")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    user_id = message.from_user.id
    now = datetime.now()

    # Получить или создать пользователя в БД
    access = await get_user_access(user_id)
    if not access:
        await create_user_access(user_id)
        access = await get_user_access(user_id)

    paid_until = access.paid_until
    trial_until = access.trial_until
    trial_activated = access.trial_activated
    trial_expired = False

    # Есть платный доступ?
    if paid_until and paid_until > now:
        await message.answer(
            "👋 Добро пожаловать! Доступ оплачен до " + paid_until.strftime("%d.%m.%Y %H:%M"),
            reply_markup=main_menu_keyboard()
        )
        return

    # Пробный уже активирован и ещё активен?
    if trial_activated and trial_until and trial_until > now:
        await message.answer(
            f"Пробный доступ активен до {trial_until.strftime('%H:%M')}\nПлатный доступ можно купить ниже.",
            reply_markup=access_keyboard(trial_active=True, trial_expired=False)
        )
        return

    # Пробный был, но истёк
    if trial_activated and trial_until and trial_until <= now:
        trial_expired = True
        await message.answer(
            "Пробный доступ уже был использован.\nКупите доступ, чтобы продолжить:",
            reply_markup=access_keyboard(trial_active=False, trial_expired=True)
        )
        return

    # Новый пользователь — показать меню доступа!
    await message.answer(
        "🔒 Для работы с ботом нужен доступ:\n"
        "— Пробный 1 час (один раз)\n"
        "— Или купить месяц за 399₽",
        reply_markup=access_keyboard(trial_active=False, trial_expired=False)
    )

# Обработка кнопки "Пробный доступ"
@router.callback_query(F.data == "trial")
async def activate_trial(callback):
    user_id = callback.from_user.id
    now = datetime.now()
    await set_trial_access(user_id, now + timedelta(hours=1))
    await callback.message.edit_text(
        "🕒 Пробный доступ активирован на 1 час!\n\n"
        "Теперь вы можете пользоваться ботом.\n"
        "Если нужен полный доступ — оплатите подписку.",
        reply_markup=access_keyboard(trial_active=True, trial_expired=False)
    )
    await callback.answer()

# Кнопка оплаты
@router.callback_query(F.data == "buy")
async def buy_access(callback):
    await callback.message.edit_text(
        "💳 Оплата пока не реализована.\n"
        "Попросите администратора выдать доступ вручную.",
        reply_markup=access_keyboard(trial_active=True, trial_expired=True)
    )
    await callback.answer()

# Кнопка пробник не активен
@router.callback_query(F.data == "trial_disabled")
async def trial_disabled(callback):
    await callback.answer("Пробный доступ уже был активирован.", show_alert=True)
