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
            InlineKeyboardButton(text="ℹ️ Информация", callback_data="main_info")
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

def access_menu_keyboard(show_trial=False, can_restore=False):
    kb = []
    if can_restore:
        kb.append([InlineKeyboardButton(text="Восстановить доступ", callback_data="restore_account")])
    elif show_trial:
        kb.append([InlineKeyboardButton(text="🕒 Пробный доступ (1 день)", callback_data="trial")])
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


def blocked_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="pay_balance")],
            [InlineKeyboardButton(text="🆘 Поддержка", callback_data="main_support")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_greeting")]
        ]
    )
def info_menu_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏬 Склады WB", callback_data="info_warehouses"),
                InlineKeyboardButton(text="📝 Инструкции", callback_data="info_instructions")
            ],
            [
                InlineKeyboardButton(text="📜 Оферта", callback_data="info_offer"),
                InlineKeyboardButton(text="🆘 Поддержка", callback_data="info_support")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main_menu")
            ]
        ]
    )

def reports_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📦 Остатки", callback_data="report_remains"),
                InlineKeyboardButton(text="📈 Продажи", callback_data="main_sales"),
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
def sales_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🛒 Отчёт по складу", callback_data="sales_by_warehouse")],
        [InlineKeyboardButton("🗃 По всем складам", callback_data="sales_by_all_warehouses")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_reports")],
    ])

def warehouses_keyboard(warehouses):
    kb = [[InlineKeyboardButton(w["name"], callback_data=f"select_warehouse:{w['id']}:{w['name']}")] for w in warehouses]
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="report_sales")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def sales_period_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("⚡ За последние 30 дней", callback_data="sales_month_fast")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="sales_by_warehouse")],
    ])

def back_to_reports_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("⬅️ К отчетам", callback_data="main_reports")]
    ])
