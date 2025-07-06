from aiogram.fsm.state import StatesGroup, State
from aiogram_calendar import SimpleCalendar
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_simple_calendar():
    return SimpleCalendar(locale="ru")

# FSM для универсального выбора периода через два SimpleCalendar
class PeriodCalendarFSM(StatesGroup):
    waiting_for_start = State()
    waiting_for_end = State()

# Кнопка "Отмена"
def cancel_calendar_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="period_calendar_cancel")]
        ]
    )

async def start_period_calendar(callback, state, period_context: dict = None):
    """Запуск FSM выбора периода. period_context — dict с нужными параметрами."""
    await state.set_state(PeriodCalendarFSM.waiting_for_start)
    if period_context:
        await state.update_data(**period_context)
    calendar = get_simple_calendar()
    kb = await calendar.start_calendar()
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="period_calendar_cancel")])
    await callback.message.edit_text(
        "<b>Выберите начальную дату периода:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

async def period_select_start(callback, callback_data, state):
    calendar = get_simple_calendar()
    is_selected, start_date = await calendar.process_selection(callback, callback_data)
    if is_selected:
        await state.update_data(period_start=start_date)
        await state.set_state(PeriodCalendarFSM.waiting_for_end)
        kb = await calendar.start_calendar()
        kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="period_calendar_cancel")])
        await callback.message.edit_text(
            f"✅ <b>Начальная дата выбрана:</b> <code>{start_date.strftime('%d.%m.%Y')}</code>\n"
            f"Теперь выберите <b>конечную дату</b> периода:",
            reply_markup=kb,
            parse_mode="HTML"
        )

async def period_select_end(callback, callback_data, state, on_finish):
    calendar = get_simple_calendar()
    is_selected, end_date = await calendar.process_selection(callback, callback_data)
    if is_selected:
        data = await state.get_data()
        start_date = data.get("period_start")
        if end_date < start_date:
            kb = await calendar.start_calendar()
            kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="period_calendar_cancel")])
            await callback.message.answer("❗ Конечная дата не может быть раньше начальной. Попробуйте снова.")
            await state.set_state(PeriodCalendarFSM.waiting_for_start)
            await callback.message.edit_text(
                "<b>Выберите начальную дату периода:</b>",
                reply_markup=kb,
                parse_mode="HTML"
            )
            return
        await callback.message.edit_text(
            f"✅ <b>Период выбран:</b> <code>{start_date.strftime('%d.%m.%Y')}</code> — <code>{end_date.strftime('%d.%m.%Y')}</code>\n"
            f"⏳ Формируем отчёт...",
            parse_mode="HTML"
        )
        await on_finish(callback, state, start_date, end_date)
        await state.clear()
