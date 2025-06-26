from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from datetime import datetime, timedelta
from bot.services.wildberries_api import get_sales_report
from storage.users import get_user_api_key

router = Router()

# Меню отчётов по продажам
def sales_main_keyboard():
    kb = [
        [InlineKeyboardButton("🛒 Все товары", callback_data="sales_all_menu")],
        [InlineKeyboardButton("🔍 По артикулам", callback_data="sales_articles_menu")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="reports_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Клавиатура выбора периода
def sales_period_keyboard():
    kb = [
        [InlineKeyboardButton("⚡ За 30 дней (быстро)", callback_data="sales_all_month_fast")],
        [InlineKeyboardButton("📆 За день", callback_data="sales_all_day")],
        [InlineKeyboardButton("🗓 За период", callback_data="sales_all_period")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="sales_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# 1. Вход через меню “Отчёты”
@router.callback_query(F.data == "sales_menu")
async def sales_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "<b>Отчёт по продажам</b>\nВыберите раздел:",
        reply_markup=sales_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# 2. “Все товары” — выбор периода
@router.callback_query(F.data == "sales_all_menu")
async def sales_all_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите период для отчёта по всем товарам:",
        reply_markup=sales_period_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

# 3. Быстрый отчёт за 30 дней (все товары)
@router.callback_query(F.data == "sales_all_month_fast")
async def sales_all_month_fast(callback: CallbackQuery):
    user_id = callback.from_user.id
    api_key = await get_user_api_key(user_id)
    if not api_key:
        await callback.message.answer("Сначала добавьте API-ключ в профиле.")
        return
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=30)
    await callback.message.answer("Формирую отчёт за последние 30 дней...")
    data = await get_sales_report(api_key, date_from.isoformat(), date_to.isoformat())
    if not data or not isinstance(data, list):
        await callback.message.answer("Нет данных за этот период.")
        return
    total = sum(item.get("forPay", 0) for item in data)
    await callback.message.answer(
        f"🛒 <b>Продажи за 30 дней</b>\n"
        f"Всего продаж: {len(data)}\n"
        f"Сумма к выплате: {total:.2f} ₽",
        parse_mode="HTML"
    )
    # — если хочешь отправить файл — добавь здесь вызов send_sales_csv(data)

# 4. За день (пользователь выбирает дату)
@router.callback_query(F.data == "sales_all_day")
async def sales_all_day(callback: CallbackQuery):
    # Можешь здесь вставить свой календарь или просто запросить дату в формате YYYY-MM-DD
    await callback.message.answer("Введите дату в формате ГГГГ-ММ-ДД для отчёта по всем товарам.")
    await callback.answer()

@router.message(F.text.regexp(r"\d{4}-\d{2}-\d{2}"))
async def sales_all_by_day(message: Message):
    user_id = message.from_user.id
    api_key = await get_user_api_key(user_id)
    date_from = date_to = message.text.strip()
    data = await get_sales_report(api_key, date_from, date_to)
    if not data or not isinstance(data, list):
        await message.answer("Нет данных за выбранную дату.")
        return
    total = sum(item.get("forPay", 0) for item in data)
    await message.answer(
        f"🛒 <b>Продажи за {date_from}</b>\n"
        f"Всего продаж: {len(data)}\n"
        f"Сумма к выплате: {total:.2f} ₽",
        parse_mode="HTML"
    )

# 5. За период (два сообщения с датами)
@router.callback_query(F.data == "sales_all_period")
async def sales_all_period(callback: CallbackQuery):
    await callback.message.answer("Введите начальную дату периода (ГГГГ-ММ-ДД):")
    await callback.answer()
    # — FSM тут поможет реализовать ввод двух дат подряд

# 6. По артикулам — меню (заготовка, нужно будет реализовать доп. фильтр)
@router.callback_query(F.data == "sales_articles_menu")
async def sales_articles_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Введите артикул (или несколько артикулов через запятую):"
    )
    await callback.answer()

@router.message(F.text.regexp(r"^[\d, ]+$"))  # простой фильтр для артикула(ов)
async def sales_by_articles(message: Message):
    user_id = message.from_user.id
    api_key = await get_user_api_key(user_id)
    articles = [art.strip() for art in message.text.split(",")]
    # Здесь цикл по артикулам — или вызови свой сервис по каждому
    result_msg = ""
    for art in articles:
        data = await get_sales_report(api_key, None, None, article=art)  # доработай get_sales_report под фильтр по артикулу
        if not data or not isinstance(data, list):
            result_msg += f"\nНет данных по артикулу {art}"
        else:
            total = sum(item.get("forPay", 0) for item in data)
            result_msg += f"\nАртикул {art}: {len(data)} продаж, {total:.2f} ₽"
    await message.answer(result_msg or "Нет данных по артикулам.")

# 7. Назад в меню отчётов
@router.callback_query(F.data == "reports_menu")
async def back_to_reports(callback: CallbackQuery):
    from bot.keyboards.inline import reports_keyboard
    await callback.message.edit_text(
        "📊 <b>Раздел отчётов</b>\n\nВыберите тип отчёта:",
        reply_markup=reports_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()