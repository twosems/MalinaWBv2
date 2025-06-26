# bot/keyboards/inline.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def reports_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📦 Остатки", callback_data="report_stock"),
                InlineKeyboardButton(text="📈 Продажи", callback_data="report_sales"),
            ],
            [
                InlineKeyboardButton(text="🏬 Хранение", callback_data="report_storage"),
                InlineKeyboardButton(text="🎯 Реклама", callback_data="report_ads"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main_menu"),
            ]
        ]
    )
