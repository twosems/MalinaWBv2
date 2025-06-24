from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from bot.keyboards.keyboards import main_menu_inline_keyboard
from storage.users import get_user_access, get_user_profile_info
from datetime import datetime

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
    )

async def main_menu(message: Message):
    user_id = message.from_user.id
    access = await get_user_access(user_id)
    user_profile = await get_user_profile_info(user_id)
    now = datetime.now()
    if not access or not access.paid_until:
        await message.answer("Нет подписки! Используйте /start.", reply_markup=ReplyKeyboardRemove())
        return
    days_left = max((access.paid_until - now).days, 0)
    balance = days_left * 13
    seller_name = user_profile.seller_name if user_profile else "—"
    trade_mark = user_profile.trade_mark if user_profile else "—"

    text = format_user_info(seller_name, trade_mark, balance, days_left, access.paid_until)
    await message.answer(text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    await message.answer("Выберите раздел:", reply_markup=main_menu_inline_keyboard())

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
