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
            [InlineKeyboardButton(text="⚙️ Настройки отчётов", callback_data="sales_report_settings")],
            [
                InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main_menu"),
            ]
        ]
    )
def sales_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Отчёт по складу", callback_data="sales_by_warehouse")],
        [InlineKeyboardButton(text="🗃 По всем складам", callback_data="sales_by_all_warehouses")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_reports")],
    ])

def warehouses_keyboard(warehouses):
    kb = [[InlineKeyboardButton(text=w["name"], callback_data=f"select_warehouse:{w['id']}:{w['name']}")] for w in warehouses]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="report_sales")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def sales_period_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ За последние 30 дней", callback_data="sales_month_fast")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="sales_by_warehouse")],
    ])

def back_to_reports_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К отчетам", callback_data="main_reports")]
    ])
def sales_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 По товарам", callback_data="sales_by_articles")],
            [InlineKeyboardButton(text="🏬 По складам", callback_data="sales_by_warehouses")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_reports")]
        ]
    )

def sales_price_type_keyboard(current_type: str) -> InlineKeyboardMarkup:
    types = [
        ("totalPrice", "Без скидок"),
        ("priceWithDisc", "Со скидкой продавца"),
        ("finishedPrice", "Фактическая для покупателя"),
        ("forPay", "К выплате продавцу"),
    ]
    ICON_SELECTED = "✅"
    ICON_UNSELECTED = "❌"
    # Считаем максимальную длину кнопки (в символах)
    max_len = max(len(v) for _, v in types)
    # Формируем кнопки с "добивкой" пробелами справа
    def pad(text):
        # +2 — запас для emoji и пробела после него
        return text + " " * (max_len - len(text) + 2)
    kb = [
        [
            InlineKeyboardButton(
                text=(f"{ICON_SELECTED}  {pad(v)}" if current_type == k else f"{ICON_UNSELECTED}  {pad(v)}"),
                callback_data=f"set_price_type:{k}"
            )
        ] for k, v in types
    ]
    kb.append([InlineKeyboardButton(text="⬅️  Назад", callback_data="sales_report_settings")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def sales_report_settings_keyboard(current_price_type: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚙️ Выбрать тип цены в отчёте",   # ← Статичный текст без текущего значения!
                callback_data="sales_price_type"
            )
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="main_reports")
        ]
    ])
def price_type_human(t):
    return {
        "totalPrice": "Без скидок",
        "priceWithDisc": "Со скидкой продавца",
        "finishedPrice": "Фактич. для покупателя",
        "forPay": "К выплате продавцу",
    }.get(t, t)

def article_mode_human(mode):
    return {
        "all": "Все артикулы",
        "in_stock": "Только с остатком",
    }.get(mode, mode)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def article_mode_human(mode):
    return {
        "all": "Все артикулы",
        "in_stock": "Только с остатком",
    }.get(mode, mode)

def articles_mode_keyboard(current_mode: str) -> InlineKeyboardMarkup:
    types = [
        ("all", "Все артикулы"),
        ("in_stock", "Только с остатком"),
    ]
    ICON_SELECTED = "✅"
    ICON_UNSELECTED = "❌"
    max_len = max(len(v) for _, v in types)
    def pad(text):
        return text + " " * (max_len - len(text) + 2)
    kb = [
        [
            InlineKeyboardButton(
                text=(f"{ICON_SELECTED}  {pad(v)}" if current_mode == k else f"{ICON_UNSELECTED}  {pad(v)}"),
                callback_data=f"set_article_mode:{k}"
            )
        ] for k, v in types
    ]
    kb.append([InlineKeyboardButton(text="⬅️  Назад", callback_data="sales_report_settings")])
    return InlineKeyboardMarkup(inline_keyboard=kb)
def sales_report_settings_keyboard(current_price_type: str, current_article_mode: str, current_warehouse_filter: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💵 Тип цены: " + price_type_human(current_price_type),
                callback_data="sales_price_type"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏷️ Артикулы: " + article_mode_human(current_article_mode),
                callback_data="articles_mode"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏬 Склады: " + warehouse_filter_human(current_warehouse_filter),
                callback_data="warehouses_filter_mode"
            )
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="main_reports")
        ]
    ])

def warehouse_filter_human(value):
    return {
        "all": "Все склады",
        "no_sc": "Без СЦ",
    }.get(value, value)

def warehouse_filter_keyboard(current: str) -> InlineKeyboardMarkup:
    types = [
        ("all", "Все склады"),
        ("no_sc", "Без СЦ"),
    ]
    ICON_SELECTED = "✅"
    ICON_UNSELECTED = "❌"
    max_len = max(len(v) for _, v in types)
    def pad(text):
        return text + " " * (max_len - len(text) + 2)
    kb = [
        [
            InlineKeyboardButton(
                text=(f"{ICON_SELECTED}  {pad(v)}" if current == k else f"{ICON_UNSELECTED}  {pad(v)}"),
                callback_data=f"set_warehouse_filter:{k}"
            )
        ] for k, v in types
    ]
    kb.append([InlineKeyboardButton(text="⬅️  Назад", callback_data="sales_report_settings")])
    return InlineKeyboardMarkup(inline_keyboard=kb)
