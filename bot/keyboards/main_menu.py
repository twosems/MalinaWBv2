from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📊 Отчёты")],
            [KeyboardButton(text="📈 Аналитика"), KeyboardButton(text="🕓 Слоты")],
            [KeyboardButton(text="📚 Инструкции"), KeyboardButton(text="🆘 Техподдержка")],
        ],
        resize_keyboard=True,
        is_persistent=True
    )
