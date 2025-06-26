from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from bot.keyboards.keyboards import main_menu_inline_keyboard
from storage.users import get_user_access, get_user_profile_info
from datetime import datetime
import logging

router = Router()

def format_user_info(seller_name, trade_mark, balance, days_left, paid_until):
    MONTHS = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    date_str = f"{paid_until.day} {MONTHS[paid_until.month-1]} {paid_until.year}"
    return (
        f"👤 <b>Профиль пользователя</b>\n"
        f"🛍️ <b>Магазин:</b> {seller_name or '—'}\n"
        f"🏷️ <b>Бренд:</b> {trade_mark or '—'}\n"
        f"\n"
        f"💰 <b>Баланс:</b> <code>{balance}₽</code>\n"
        f"⏳ <b>Осталось дней:</b> <code>{days_left}</code>\n"
        f"📅 <b>Подписка до:</b> <code>{date_str}</code>\n"
        f"\n"
        f"<b>Выберите раздел:</b>"
    )

async def main_menu(message: Message):
    user_id = message.from_user.id
    access = await get_user_access(user_id)
    user_profile = await get_user_profile_info(user_id)
    now = datetime.utcnow()

    # --- ОТЛАДКА: показываем состояние access
    if access is None:
        debug_text = "<b>DEBUG main_menu:</b>\naccess: <code>None</code>"
        logging.info(f"[DEBUG main_menu] user_id={user_id} access=None")
        await message.answer(debug_text, parse_mode="HTML")
        from aiogram.types import ReplyKeyboardRemove
        await message.answer("Нет подписки! Используйте /start.", reply_markup=ReplyKeyboardRemove())
        return

    debug_text = (
        "<b>DEBUG main_menu:</b>\n"
        f"paid_until: <code>{access.paid_until} [{type(access.paid_until)}]</code>\n"
        f"trial_until: <code>{access.trial_until} [{type(access.trial_until)}]</code>\n"
        f"now: <code>{now} [{type(now)}]</code>"
    )
    logging.info(f"[DEBUG main_menu] user_id={user_id} paid_until={access.paid_until} ({type(access.paid_until)}) "
                 f"trial_until={access.trial_until} ({type(access.trial_until)}) now={now} ({type(now)})")
    if message.chat.type == "private":
        await message.answer(debug_text, parse_mode="HTML")

    # Проверка: есть ли платная подписка или активный trial
    trial_active = (
            getattr(access, "trial_activated", False)
            and getattr(access, "trial_until", None)
            and access.trial_until and access.trial_until > now
    )
    paid_active = (
            access.paid_until and access.paid_until > now
    )

    if not paid_active and not trial_active:
        from aiogram.types import ReplyKeyboardRemove
        await message.answer("Нет подписки! Используйте /start.", reply_markup=ReplyKeyboardRemove())
        return

    # Считаем оставшиеся дни и дату окончания доступа (trial или подписка)
    if paid_active:
        days_left = max((access.paid_until - now).days, 0)
        access_until = access.paid_until
    else:
        days_left = max((access.trial_until - now).days, 0)
        access_until = access.trial_until

    balance = days_left * 13
    seller_name = user_profile.seller_name if user_profile else "—"
    trade_mark = user_profile.trade_mark if user_profile else "—"

    text = format_user_info(seller_name, trade_mark, balance, days_left, access_until)
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_inline_keyboard())

# Остальные callback_handlers без изменений:

@router.callback_query(F.data == "main_profile")
async def main_profile(callback: CallbackQuery):
    from bot.handlers.profile import profile_menu
    await callback.message.delete()
    await profile_menu(callback.message)

@router.callback_query(F.data == "main_reports")
async def reports_menu(callback: CallbackQuery):
    await callback.answer("Здесь будет раздел отчётов.", show_alert=True)

@router.callback_query(F.data == "main_analytics")
async def analytics_menu(callback: CallbackQuery):
    await callback.answer("Здесь будет раздел аналитики.", show_alert=True)

@router.callback_query(F.data == "main_slots")
async def slots_menu(callback: CallbackQuery):
    await callback.answer("Здесь будет раздел слотов.", show_alert=True)

@router.callback_query(F.data == "main_support")
async def support_menu(callback: CallbackQuery):
    await callback.answer("Здесь будет поддержка.", show_alert=True)

@router.callback_query(F.data == "main_instructions")
async def instructions_menu(callback: CallbackQuery):
    await callback.answer("Здесь будут инструкции.", show_alert=True)
