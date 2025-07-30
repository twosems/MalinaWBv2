from aiogram.fsm.state import StatesGroup, State
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

class PeriodCalendarFSM(StatesGroup):
    waiting_for_start = State()
    waiting_for_end = State()

class DayCalendarFSM(StatesGroup):
    choosing_day = State()

def get_simple_calendar():
    return SimpleCalendar(locale="ru")

def cancel_keyboard(cancel_callback):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback)]]
    )

def quick_periods_keyboard():
    return [[
        InlineKeyboardButton(text="🗓 7 дней", callback_data="quick_period_7"),
        InlineKeyboardButton(text="🗓 30 дней", callback_data="quick_period_30"),
        InlineKeyboardButton(text="🗓 Текущий месяц", callback_data="quick_period_month"),
    ]]

# === Календарь "Период" ===
async def start_period_calendar(callback, state, period_context: dict = None, on_finish=None):
    await state.set_state(PeriodCalendarFSM.waiting_for_start)
    if period_context:
        await state.update_data(**period_context)
    await state.update_data(on_finish=on_finish)
    calendar = get_simple_calendar()
    kb = await calendar.start_calendar()
    kb.inline_keyboard = quick_periods_keyboard() + kb.inline_keyboard
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="period_calendar_cancel")])
    await callback.message.edit_text(
        "<b>Выберите начальную дату периода:</b>\nИли воспользуйтесь быстрым выбором 👇",
        reply_markup=kb, parse_mode="HTML"
    )

async def period_select_start(callback, callback_data: SimpleCalendarCallback, state):
    calendar = get_simple_calendar()
    is_selected, start_date = await calendar.process_selection(callback, callback_data)
    if is_selected:
        await state.update_data(period_start=start_date)
        await state.set_state(PeriodCalendarFSM.waiting_for_end)
        kb = await calendar.start_calendar()
        kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="period_calendar_cancel")])
        await callback.message.edit_text(
            f"✅ <b>Начальная дата:</b> <code>{start_date.strftime('%d.%m.%Y')}</code>\n<b>Теперь выберите конец.</b>",
            reply_markup=kb,
            parse_mode="HTML"
        )

async def period_select_end(callback, callback_data: SimpleCalendarCallback, state):
    calendar = get_simple_calendar()
    is_selected, end_date = await calendar.process_selection(callback, callback_data)
    if is_selected:
        data = await state.get_data()
        start_date = data.get("period_start")
        on_finish = data.get("on_finish")
        if end_date < start_date:
            await callback.message.answer("⚠️ Конец должен быть позже начала.")
            return await start_period_calendar(callback, state, on_finish=on_finish)
        await callback.message.edit_text(
            f"✅ <b>Выбрано:</b> <code>{start_date.strftime('%d.%m.%Y')}</code> — <code>{end_date.strftime('%d.%m.%Y')}</code>\n⏳ Готовим...",
            parse_mode="HTML"
        )
        if on_finish:
            await on_finish(callback, state, start_date, end_date)

# === Быстрые периоды ===
async def quick_period_handler(callback, state, days: int = None, this_month: bool = False):
    date_to = datetime.now().date()
    if this_month:
        date_from = date_to.replace(day=1)
    elif days:
        date_from = date_to - timedelta(days=days)
    else:
        date_from = date_to - timedelta(days=7)
    data = await state.get_data()
    on_finish = data.get("on_finish")
    await callback.message.edit_text(
        f"✅ <b>Выбрано:</b> <code>{date_from.strftime('%d.%m.%Y')}</code> — <code>{date_to.strftime('%d.%m.%Y')}</code>\n⏳ Готовим...",
        parse_mode="HTML"
    )
    if on_finish:
        await on_finish(callback, state, date_from, date_to)

# === Календарь "Один день" ===
async def start_day_calendar(callback, state, context: dict = None, text="Выберите дату", on_finish=None):
    await state.set_state(DayCalendarFSM.choosing_day)
    if context:
        await state.update_data(**context)
    await state.update_data(on_finish=on_finish)
    calendar = get_simple_calendar()
    kb = await calendar.start_calendar()
    today = datetime.now().date().isoformat()
    kb.inline_keyboard.insert(0, [InlineKeyboardButton(text="🗓 Сегодня", callback_data=f"calendar:{today}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="calendar_day_cancel")])
    await callback.message.edit_text(f"🗓 <b>{text}</b>", reply_markup=kb, parse_mode="HTML")

async def day_selected(callback, callback_data, state):
    calendar = get_simple_calendar()
    is_selected, date = await calendar.process_selection(callback, callback_data)
    data = await state.get_data()
    on_finish = data.get("on_finish")
    if is_selected:
        await callback.message.edit_text(f"✅ <b>Дата:</b> <code>{date.strftime('%d.%m.%Y')}</code>\n⏳ Готовим...", parse_mode="HTML")
        if on_finish:
            await on_finish(callback, state, date, date)
def remove_builtin_calendar_buttons(kb):
    # Удалить последнюю строку, если в ней есть Cancel, Today или пустая кнопка
    if kb.inline_keyboard and len(kb.inline_keyboard) > 0:
        new_keyboard = []
        for row in kb.inline_keyboard:
            if not any(btn.text in ["Cancel", "Today", None, ""] for btn in row if hasattr(btn, 'text')):
                new_keyboard.append(row)
        kb.inline_keyboard = new_keyboard
    return kb
