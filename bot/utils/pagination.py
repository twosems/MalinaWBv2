from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def build_pagination_keyboard(total, page, per_page, prefix, back_callback, add_export=False):
    pages = max(1, (total + per_page - 1) // per_page)
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️ Предыдущая", callback_data=f"{prefix}{page-1}"))
    if page < pages:
        nav.append(InlineKeyboardButton(text="Следующая ➡️", callback_data=f"{prefix}{page+1}"))
    kb = []
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data=back_callback)])
    if add_export:
        kb.append([InlineKeyboardButton(text="⬇️ Экспорт в CSV", callback_data="report_remains_export_csv")])
    return InlineKeyboardMarkup(inline_keyboard=kb)
