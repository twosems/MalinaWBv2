from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.keyboards.keyboards import info_menu_inline_keyboard
from bot.utils.pagination import build_pagination_keyboard
from storage.warehouses import get_cached_warehouses_dicts

router = Router()
PER_PAGE = 10

@router.callback_query(F.data == "main_info")
async def info_menu(callback: CallbackQuery):
    text = (
        "ℹ️ <b>Информация и справка</b>\n\n"
        "🏬 <b>Склады WB</b> — кеш адресов складов, быстрая проверка, обновление вручную\n"
        "📝 <b>Инструкции</b> — руководство пользователя, подключение, FAQ\n"
        "📜 <b>Оферта</b> — правила и условия использования сервиса\n"
        "🆘 <b>Поддержка</b> — вопросы, обратная связь, помощь\n\n"
        "<i>Выберите нужный раздел:</i>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=info_menu_inline_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.regexp(r"^info_warehouses(_page_)?(\d+)?$"))
async def info_warehouses(callback: CallbackQuery):
    import re
    m = re.match(r"^info_warehouses(?:_page_)?(\d+)?$", callback.data)
    page = int(m.group(1)) if m and m.group(1) else 1

    warehouses = await get_cached_warehouses_dicts()
    total = len(warehouses)
    pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    page_warehouses = warehouses[start:end]

    if not page_warehouses:
        text = "⛔️ Нет складов для отображения."
    else:
        text = f"🏬 <b>Склады Wildberries</b>\n\n"
        for wh in page_warehouses:
            name = wh.get("name", "Без названия")
            address = wh.get("address", "") or ""
            status = "🟢 Активен" if wh.get("isActive") else "🔴 Не активен"
            text += f"<b>{name}</b>\n"
            if address:
                text += f"📍 <i>{address}</i>\n"
            text += f"{status}\n\n"
        text += f"<b>Страница {page} из {pages}</b>"

    kb = build_pagination_keyboard(
        total=total,
        page=page,
        per_page=PER_PAGE,
        prefix="info_warehouses_page_",
        back_callback="main_info"
    )

    await callback.message.edit_text(
        text,
        reply_markup=kb,
        parse_mode="HTML"
    )

# Аналогично можешь добавить:
# @router.callback_query(F.data == "info_instructions")
# @router.callback_query(F.data == "info_offer")
# @router.callback_query(F.data == "info_support")
