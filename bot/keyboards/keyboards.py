from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def guest_menu():
    # "Продолжить" как inline-кнопка!
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Продолжить", callback_data="guest_continue")]
        ]
    )

def main_menu_inline_keyboard():
    # Главное меню: 2 столбца, 3 ряда (в каждой строке по 2 кнопки)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Отчёты", callback_data="main_reports"),
            InlineKeyboardButton(text="📅 Слоты", callback_data="main_slots")
        ],
        [
            InlineKeyboardButton(text="📈 Аналитика", callback_data="main_analytics"),
            InlineKeyboardButton(text="📖 Инструкции", callback_data="main_instructions")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="main_profile"),
            InlineKeyboardButton(text="🆘 Поддержка", callback_data="main_support")
        ]
    ])

def profile_keyboard(has_api=True):
    if has_api:
        kb = [
            [KeyboardButton(text="Удалить API")],
            [KeyboardButton(text="Удалить пользователя")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    else:
        kb = [
            [KeyboardButton(text="Ввести API")],
            [KeyboardButton(text="Удалить пользователя")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def access_menu_keyboard(trial_active=False, trial_expired=False, show_trial=True):
    kb = []
    if show_trial:
        if not trial_active and not trial_expired:
            kb.append([InlineKeyboardButton(text="🕒 Пробный доступ (1 час)", callback_data="trial")])
        else:
            label = "🕒 Пробный доступ (уже активирован)" if trial_expired else "🕒 Пробный доступ (активен)"
            kb.append([InlineKeyboardButton(text=label, callback_data="trial_disabled")])
    kb.append([InlineKeyboardButton(text="💳 Оплатить доступ 399₽/мес", callback_data="buy")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_greeting")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def profile_api_fail_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True
    )
