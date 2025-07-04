from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from storage.warehouses import get_cached_warehouses_dicts
from storage.users import get_user_api_key
from utils.pagination import build_pagination_keyboard
from utils.calendar import get_simple_calendar, SimpleCalendarCallback, get_dialog_calendar, DialogCalendarCallback
from utils.csv_export import export_to_csv
import aiohttp
from datetime import datetime, timedelta

router = Router()
PAGE_SIZE_WAREHOUSES = 10
PAGE_SIZE_ARTICLES = 10

# ============ ГЛАВНОЕ МЕНЮ ПРОДАЖ ============
@router.callback_query(F.data == "main_sales")
async def sales_main_menu(callback: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🛒 Отчёт по складу", callback_data="sales_by_warehouse_menu")],
        [InlineKeyboardButton(text="🔍 Отчёт по артикулам", callback_data="sales_by_article_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu")]
    ]
    await callback.message.edit_text(
        "<b>Отчёт по продажам</b>\nВыберите раздел:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# ============ ПО СКЛАДУ ============
@router.callback_query(F.data == "sales_by_warehouse_menu")
async def sales_by_warehouse_menu(callback: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="По складу", callback_data="sales_warehouse_select:1")],
        [InlineKeyboardButton(text="По всем складам", callback_data="sales_all_warehouses_period")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_sales")]
    ]
    await callback.message.edit_text(
        "<b>Продажи: по складу или по всем?</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# --- Список складов с пагинацией ---
@router.callback_query(F.data.startswith("sales_warehouse_select:"))
async def sales_warehouse_select(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    warehouses = await get_cached_warehouses_dicts()
    total = len(warehouses)
    pages = max(1, (total + PAGE_SIZE_WAREHOUSES - 1) // PAGE_SIZE_WAREHOUSES)
    page = max(1, min(page, pages))
    start = (page - 1) * PAGE_SIZE_WAREHOUSES
    end = start + PAGE_SIZE_WAREHOUSES
    items = warehouses[start:end]

    kb = [
        [InlineKeyboardButton(text=w['name'], callback_data=f"sales_warehouse_period_menu:{w['id']}")]
        for w in items
    ]
    nav_kb = build_pagination_keyboard(total, page, PAGE_SIZE_WAREHOUSES, "sales_warehouse_select:", "sales_by_warehouse_menu")
    kb.extend(nav_kb.inline_keyboard)

    await callback.message.edit_text(
        f"Выберите склад ({page}/{pages}):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# --- После выбора склада — выбор периода ---
@router.callback_query(F.data.startswith("sales_warehouse_period_menu:"))
async def sales_warehouse_period_menu(callback: CallbackQuery, state: FSMContext):
    warehouse_id = callback.data.split(":")[1]
    await state.update_data(sales_warehouse_id=warehouse_id)
    kb = [
        [InlineKeyboardButton(text="⚡ За последние 30 дней", callback_data="sales_warehouse_last30")],
        [InlineKeyboardButton(text="📆 За день", callback_data="sales_warehouse_day")],
        [InlineKeyboardButton(text="🗓 За период", callback_data="sales_warehouse_period")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="sales_warehouse_select:1")],
    ]
    await callback.message.edit_text(
        "<b>Выберите период:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# --- За последние 30 дней ---
@router.callback_query(F.data == "sales_warehouse_last30")
async def sales_warehouse_last30(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    warehouse_id = user_data.get("sales_warehouse_id")
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=30)
    await show_sales_report(callback, warehouse_id, date_from, date_to, by_warehouse=True, state=state)

# --- За день (через календарь) ---
@router.callback_query(F.data == "sales_warehouse_day")
async def sales_warehouse_day(callback: CallbackQuery):
    calendar = get_simple_calendar()
    await callback.message.edit_text(
        "<b>Выберите день:</b>",
        reply_markup=await calendar.start_calendar(),
        parse_mode="HTML"
    )

@router.callback_query(SimpleCalendarCallback.filter())
async def sales_warehouse_day_calendar(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    calendar = get_simple_calendar()
    is_selected, date = await calendar.process_selection(callback, callback_data)
    if is_selected:
        user_data = await state.get_data()
        warehouse_id = user_data.get("sales_warehouse_id")
        await show_sales_report(callback, warehouse_id, date, date, by_warehouse=True, state=state)

# --- За период (диапазон через календарь) ---
@router.callback_query(F.data == "sales_warehouse_period")
async def sales_warehouse_period(callback: CallbackQuery):
    calendar = get_dialog_calendar()
    await callback.message.edit_text(
        "<b>Выберите период:</b>",
        reply_markup=await calendar.start_calendar(),
        parse_mode="HTML"
    )

@router.callback_query(DialogCalendarCallback.filter())
async def sales_warehouse_period_calendar(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    calendar = get_dialog_calendar()
    result = await calendar.process_selection(callback, callback_data)
    if len(result) == 3:
        is_selected, date_from, date_to = result
        if is_selected:
            user_data = await state.get_data()
            warehouse_id = user_data.get("sales_warehouse_id")
            await show_sales_report(callback, warehouse_id, date_from, date_to, by_warehouse=True, state=state)
    else:
        is_selected, _ = result
        # Просто ничего не делаем, ждем следующий клик по календарю
        return


# ============ ПО ВСЕМ СКЛАДАМ ============
@router.callback_query(F.data == "sales_all_warehouses_period")
async def sales_all_warehouses_period(callback: CallbackQuery, state: FSMContext):
    kb = [
        [InlineKeyboardButton(text="⚡ За последние 30 дней", callback_data="sales_all_warehouses_last30")],
        [InlineKeyboardButton(text="📆 За день", callback_data="sales_all_warehouses_day")],
        [InlineKeyboardButton(text="🗓 За период", callback_data="sales_all_warehouses_dialog")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="sales_by_warehouse_menu")]
    ]
    await callback.message.edit_text(
        "<b>Период для отчёта по всем складам:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "sales_all_warehouses_last30")
async def sales_all_warehouses_last30(callback: CallbackQuery, state: FSMContext):
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=30)
    await show_sales_report(callback, None, date_from, date_to, by_warehouse=True, all_warehouses=True, state=state)

@router.callback_query(F.data == "sales_all_warehouses_day")
async def sales_all_warehouses_day(callback: CallbackQuery):
    calendar = get_simple_calendar()
    await callback.message.edit_text(
        "<b>Выберите день:</b>",
        reply_markup=await calendar.start_calendar(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "sales_all_warehouses_dialog")
async def sales_all_warehouses_dialog(callback: CallbackQuery):
    calendar = get_dialog_calendar()
    await callback.message.edit_text(
        "<b>Выберите период:</b>",
        reply_markup=await calendar.start_calendar(),
        parse_mode="HTML"
    )

# ============ ПО АРТИКУЛАМ ============
@router.callback_query(F.data == "sales_by_article_menu")
async def sales_by_article_menu(callback: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🟢 Только артикулы с остатком", callback_data="sales_articles_in_stock:1")],
        [InlineKeyboardButton(text="📋 Все доступные артикулы", callback_data="sales_articles_all:1")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_sales")]
    ]
    await callback.message.edit_text(
        "<b>Отчёт по артикулам:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

from bot.services.wildberries_api import get_stocks

@router.callback_query(F.data.startswith("sales_articles_in_stock:"))
async def sales_articles_in_stock(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    api_key = await get_user_api_key(user_id)
    stocks = await get_stocks(api_key)
    arts = sorted(set(i["supplierArticle"] for i in stocks if i.get("quantity", 0) > 0))
    total = len(arts)
    pages = max(1, (total + PAGE_SIZE_ARTICLES - 1) // PAGE_SIZE_ARTICLES)
    page = max(1, min(page, pages))
    start = (page - 1) * PAGE_SIZE_ARTICLES
    end = start + PAGE_SIZE_ARTICLES
    items = arts[start:end]

    kb = [
        [InlineKeyboardButton(text=art, callback_data=f"sales_article_period_menu:{art}")]
        for art in items
    ]
    nav_kb = build_pagination_keyboard(total, page, PAGE_SIZE_ARTICLES, "sales_articles_in_stock:", "sales_by_article_menu")
    kb.extend(nav_kb.inline_keyboard)

    await callback.message.edit_text(
        f"Выберите артикул ({page}/{pages}):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

@router.callback_query(F.data.startswith("sales_articles_all:"))
async def sales_articles_all(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    api_key = await get_user_api_key(user_id)
    stocks = await get_stocks(api_key)
    arts = sorted(set(i["supplierArticle"] for i in stocks))
    total = len(arts)
    pages = max(1, (total + PAGE_SIZE_ARTICLES - 1) // PAGE_SIZE_ARTICLES)
    page = max(1, min(page, pages))
    start = (page - 1) * PAGE_SIZE_ARTICLES
    end = start + PAGE_SIZE_ARTICLES
    items = arts[start:end]

    kb = [
        [InlineKeyboardButton(text=art, callback_data=f"sales_article_period_menu:{art}")]
        for art in items
    ]
    nav_kb = build_pagination_keyboard(total, page, PAGE_SIZE_ARTICLES, "sales_articles_all:", "sales_by_article_menu")
    kb.extend(nav_kb.inline_keyboard)

    await callback.message.edit_text(
        f"Выберите артикул ({page}/{pages}):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

# --- После выбора артикула — период ---
@router.callback_query(F.data.startswith("sales_article_period_menu:"))
async def sales_article_period_menu(callback: CallbackQuery, state: FSMContext):
    art = callback.data.split(":")[1]
    await state.update_data(sales_article=art)
    kb = [
        [InlineKeyboardButton(text="⚡ За последние 30 дней", callback_data="sales_article_last30")],
        [InlineKeyboardButton(text="📆 За день", callback_data="sales_article_day")],
        [InlineKeyboardButton(text="🗓 За период", callback_data="sales_article_period")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="sales_by_article_menu")],
    ]
    await callback.message.edit_text(
        f"<b>Артикул:</b> <code>{art}</code>\nВыберите период:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# --- Артикул — периоды ---
@router.callback_query(F.data == "sales_article_last30")
async def sales_article_last30(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    art = user_data.get("sales_article")
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=30)
    await show_sales_article_report(callback, art, date_from, date_to, state=state)

@router.callback_query(F.data == "sales_article_day")
async def sales_article_day(callback: CallbackQuery):
    calendar = get_simple_calendar()
    await callback.message.edit_text(
        "<b>Выберите день:</b>",
        reply_markup=await calendar.start_calendar(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "sales_article_period")
async def sales_article_period(callback: CallbackQuery):
    calendar = get_dialog_calendar()
    await callback.message.edit_text(
        "<b>Выберите период:</b>",
        reply_markup=await calendar.start_calendar(),
        parse_mode="HTML"
    )

# --- Календарь: день/период для артикула ---
@router.callback_query(SimpleCalendarCallback.filter())
async def sales_article_day_calendar(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    calendar = get_simple_calendar()
    is_selected, date = await calendar.process_selection(callback, callback_data)
    if is_selected:
        user_data = await state.get_data()
        art = user_data.get("sales_article")
        await show_sales_article_report(callback, art, date, date, state=state)

@router.callback_query(DialogCalendarCallback.filter())
async def sales_article_period_calendar(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    calendar = get_dialog_calendar()
    is_selected, date_from, date_to = await calendar.process_selection(callback, callback_data)
    if is_selected:
        user_data = await state.get_data()
        art = user_data.get("sales_article")
        await show_sales_article_report(callback, art, date_from, date_to, state=state)

# ============ ОТЧЁТ ПО СКЛАДУ ============
async def show_sales_report(callback, warehouse_id, date_from, date_to, by_warehouse=False, all_warehouses=False, state=None):
    user_id = callback.from_user.id
    api_key = await get_user_api_key(user_id)
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
    headers = {"Authorization": api_key}
    params = {"dateFrom": date_from.strftime("%Y-%m-%d"), "dateTo": date_to.strftime("%Y-%m-%d")}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status != 200:
                await callback.message.answer("Ошибка WB API, проверьте токен.")
                return
            sales = await resp.json()
    warehouses = await get_cached_warehouses_dicts()

    text = ""
    total_sum = 0
    total_qty = 0
    export_rows = []

    if all_warehouses:
        wh_groups = {}
        for s in sales:
            wh_id = str(s.get("warehouseId"))
            wh_groups.setdefault(wh_id, []).append(s)
        for wh_id, group in wh_groups.items():
            wh = next((w for w in warehouses if str(w["id"]) == wh_id), {})
            wh_name = wh.get("name", f"ID {wh_id}")
            text += f"\n<b>Склад: {wh_name}</b>\n"
            stat = {}
            for item in group:
                art = item.get("supplierArticle", "—")
                price = item.get("priceWithDisc", 0)
                stat.setdefault(art, {"qty": 0, "price": price, "sum": 0})
                stat[art]["qty"] += 1
                stat[art]["sum"] += price
            for art, st in stat.items():
                text += f"{art}: {st['qty']} × {st['price']} = {st['sum']:.2f}\n"
                total_sum += st["sum"]
                total_qty += st["qty"]
                export_rows.append([wh_name, art, st["qty"], st["price"], st["sum"]])
            text += f"<b>Итого: {sum(s['qty'] for s in stat.values())} шт / {sum(s['sum'] for s in stat.values()):.2f} ₽</b>\n"
    else:
        wh = next((w for w in warehouses if str(w["id"]) == str(warehouse_id)), {})
        wh_name = wh.get("name", f"ID {warehouse_id}")
        filtered_sales = [s for s in sales if str(s.get("warehouseId")) == str(warehouse_id)]
        stat = {}
        for item in filtered_sales:
            art = item.get("supplierArticle", "—")
            price = item.get("priceWithDisc", 0)
            stat.setdefault(art, {"qty": 0, "price": price, "sum": 0})
            stat[art]["qty"] += 1
            stat[art]["sum"] += price
        text += f"📦 <b>Продажи по складу: {wh_name}</b>\n"
        text += f"🗓 <b>Период:</b> {date_from} — {date_to}\n\n"
        total_qty = sum(st["qty"] for st in stat.values())
        total_sum = sum(st["sum"] for st in stat.values())
        for art, st in stat.items():
            text += f"{art}: {st['qty']} × {st['price']} = {st['sum']:.2f}\n"
            export_rows.append([wh_name, art, st["qty"], st["price"], st["sum"]])
        text += f"\n<b>Итого: {total_qty} шт, {total_sum:.2f} ₽</b>\n"

    kb = [
        [InlineKeyboardButton(text="📥 Экспорт в CSV", callback_data="sales_export_csv")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="sales_by_warehouse_menu")]
    ]
    await callback.message.answer(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

    # Сохраняем в state для экспорта
    if state is not None:
        await state.update_data(sales_export_rows=export_rows)

# ============ ОТЧЁТ ПО АРТИКУЛУ ============
async def show_sales_article_report(callback, art, date_from, date_to, state=None):
    user_id = callback.from_user.id
    api_key = await get_user_api_key(user_id)
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
    headers = {"Authorization": api_key}
    params = {"dateFrom": date_from.strftime("%Y-%m-%d"), "dateTo": date_to.strftime("%Y-%m-%d")}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status != 200:
                await callback.message.answer("Ошибка WB API, проверьте токен.")
                return
            sales = await resp.json()
    warehouses = await get_cached_warehouses_dicts()

    filtered = [s for s in sales if s.get("supplierArticle") == art]
    wh_stat = {}
    total_sum = 0
    total_qty = 0
    export_rows = []

    for item in filtered:
        wh_id = str(item.get("warehouseId"))
        wh = next((w for w in warehouses if str(w["id"]) == wh_id), {})
        wh_name = wh.get("name", f"ID {wh_id}")
        price = item.get("priceWithDisc", 0)
        wh_stat.setdefault(wh_name, {"qty": 0, "sum": 0})
        wh_stat[wh_name]["qty"] += 1
        wh_stat[wh_name]["sum"] += price

    text = f"🔍 <b>Отчёт по артикулу: {art}</b>\nПериод: {date_from} — {date_to}\n\n"
    for wh_name, st in wh_stat.items():
        text += f"{wh_name}: {st['qty']} шт / {st['sum']:.2f} ₽\n"
        total_sum += st['sum']
        total_qty += st['qty']
        export_rows.append([wh_name, art, st['qty'], st['sum']])
    text += f"\n<b>Итого: {total_qty} шт, {total_sum:.2f} ₽</b>"

    kb = [
        [InlineKeyboardButton(text="📥 Экспорт в CSV", callback_data="sales_article_export_csv")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="sales_by_article_menu")]
    ]
    await callback.message.answer(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    if state is not None:
        await state.update_data(sales_export_rows=export_rows)

# ============ ЭКСПОРТ В CSV ============
@router.callback_query(F.data == "sales_export_csv")
async def sales_export_csv(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    export_rows = user_data.get("sales_export_rows")
    if not export_rows:
        await callback.message.answer("Нет данных для экспорта.")
        return
    columns = ["Склад", "Артикул", "Кол-во", "Цена", "Сумма"]
    file = export_to_csv(export_rows, columns, filename="sales_report.csv")
    await callback.message.answer_document(file)

@router.callback_query(F.data == "sales_article_export_csv")
async def sales_article_export_csv(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    export_rows = user_data.get("sales_export_rows")
    if not export_rows:
        await callback.message.answer("Нет данных для экспорта.")
        return
    columns = ["Склад", "Артикул", "Кол-во", "Сумма"]
    file = export_to_csv(export_rows, columns, filename="sales_article_report.csv")
    await callback.message.answer_document(file)
