# bot/keyboards/inline.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def reports_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Остатки товара", callback_data="remains_menu")],
            [InlineKeyboardButton(text="💸 Отчёт по продажам", callback_data="sales_menu")],
            [InlineKeyboardButton(text="📣 Отчёт по рекламе", callback_data="ads_menu")],
            [InlineKeyboardButton(text="💼 Отчёт о хранении", callback_data="storage_entry")],
            [InlineKeyboardButton(text="💰 Отчёт по прибыли", callback_data="profit_menu")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="account_menu")],
        ]
    )
