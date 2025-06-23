"""
profile.py — хендлеры для профиля пользователя Telegram-бота.

Функции:
- Проверка и предоставление доступа (оплачен, пробный, заблокирован)
- Обработка пробного периода и предложений по оплате
- Сохранение и получение Wildberries API-ключа пользователя (через команду или кнопку)
- Основное меню профиля

Использует асинхронные функции из storage.users для работы с БД:
    - get_user_access
    - set_trial_access
    - create_user_access
    - set_user_api_key
    - get_user_api_key

Интерфейс:
- Кнопка "👤 Профиль" открывает меню профиля и позволяет сохранить или получить свой API-ключ
- Сообщение "API <ключ>" сохраняет API-ключ для пользователя
- Кнопка "Мой API ключ" возвращает сохранённый API-ключ
"""

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
from storage.users import (
    get_user_access,
    set_trial_access,
    create_user_access,
    set_user_api_key,
    get_user_api_key
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

def profile_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мой API ключ")],
            [KeyboardButton(text="Ввести API ключ")],
            [KeyboardButton(text="⬅️ Назад")],
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

    # Получаем/создаём доступ пользователя из базы
    access = await get_user_access(user_id)
    if not access:
        await create_user_access(user_id)
        access = await get_user_access(user_id)

    paid_until = access.paid_until
    trial_until = access.trial_until
    trial_activated = access.trial_activated

    if paid_until and paid_until > now:
        await message.answer(
            f"👋 Добро пожаловать! Доступ оплачен до {paid_until.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=main_menu_keyboard()
        )
        return

    if trial_activated and trial_until and trial_until > now:
        await message.answer(
            f"👋 Пробный доступ активен до {trial_until.strftime('%H:%M')}.\nДобро пожаловать!",
            reply_markup=main_menu_keyboard()
        )
        return

    if trial_activated and trial_until and trial_until <= now:
        await message.answer(
            "Пробный доступ уже был использован.\nКупите доступ, чтобы продолжить:",
            reply_markup=access_keyboard(trial_active=False, trial_expired=True)
        )
        return

    await message.answer(
        "🔒 Для работы с ботом нужен доступ:\n— Пробный 1 час (один раз)\n— Или купить месяц за 399₽",
        reply_markup=access_keyboard(trial_active=False, trial_expired=False)
    )

@router.callback_query(F.data == "trial")
async def activate_trial(callback):
    user_id = callback.from_user.id
    now = datetime.now()
    await set_trial_access(user_id, now + timedelta(hours=1))

    await callback.message.edit_text(
        "🕒 Пробный доступ активирован на 1 час!\n\n"
        "Теперь вы можете пользоваться ботом.\n"
        "Если нужен полный доступ — оплатите подписку."
    )
    await callback.message.answer(
        "👋 Главное меню:",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "buy")
async def buy_access(callback):
    await callback.message.edit_text(
        "💳 Оплата пока не реализована.\n"
        "Попросите администратора выдать доступ вручную.",
        reply_markup=access_keyboard(trial_active=True, trial_expired=True)
    )
    await callback.answer()

@router.callback_query(F.data == "trial_disabled")
async def trial_disabled(callback):
    await callback.answer("Пробный доступ уже был активирован.", show_alert=True)

# === Добавляем обработку API-ключа ===

# Обработка команды или кнопки "Ввести API ключ"
@router.message(F.text == "Ввести API ключ")
async def ask_for_api_key(message: Message):
    await message.answer("Пожалуйста, отправьте свой Wildberries API-ключ в формате:\n\nAPI <ваш_ключ>")

# Обработка сообщения для сохранения API-ключа (ожидает "API <ключ>")
@router.message(F.text.regexp(r"^API\s+(.+)"))
async def save_api_key(message: Message):
    user_id = message.from_user.id
    api_key = message.text.split(' ', 1)[1].strip()
    await set_user_api_key(user_id, api_key)
    await message.answer("✅ Ваш API-ключ успешно сохранён!", reply_markup=profile_menu_keyboard())

# Кнопка "Мой API ключ" — показать сохранённый API-ключ
@router.message(F.text == "Мой API ключ")
async def show_api_key(message: Message):
    user_id = message.from_user.id
    api_key = await get_user_api_key(user_id)
    if api_key:
        await message.answer(f"Ваш сохранённый API-ключ:\n<code>{api_key}</code>", reply_markup=profile_menu_keyboard())
    else:
        await message.answer("У вас ещё не сохранён API-ключ.\n\nИспользуйте кнопку 'Ввести API ключ'.", reply_markup=profile_menu_keyboard())

# Профиль (кнопка)
@router.message(F.text == "👤 Профиль")
async def profile_menu(message: Message):
    await message.answer(
        "Меню профиля:\n\n"
        "- Можешь посмотреть или изменить свой Wildberries API-ключ\n"
        "- Для смены ключа просто отправь новый (API <ключ>)",
        reply_markup=profile_menu_keyboard()
    )
