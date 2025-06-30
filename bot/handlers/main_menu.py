from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.handlers import start, reports, profile, admin, api_entry, main_menu
from bot.keyboards.keyboards import main_menu_inline_keyboard, access_menu_keyboard
from storage.users import get_user_access, get_user_profile_info
from datetime import datetime
from aiogram.fsm.context import FSMContext
import logging

router = Router()

def format_user_info(seller_name, balance, days_left, paid_until, registration_date=None):
    MONTHS = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    date_str = f"{paid_until.day} {MONTHS[paid_until.month-1]} {paid_until.year}"
    reg_str = f"\n🗓️ <b>Зарегистрирован:</b> <code>{format_registration_date(registration_date)}</code>" if registration_date else ""
    return (
        f"👤 <b>Профиль пользователя</b>\n"
        f"🛍️ <b>Магазин:</b> {seller_name or '—'}\n"
        f"💰 <b>Баланс:</b> <code>{balance}₽</code>\n"
        f"⏳ <b>Осталось дней:</b> <code>{days_left}</code>\n"
        f"📅 <b>Подписка до:</b> <code>{date_str}</code>"
        f"{reg_str}\n"
        f"\n<b>Выберите раздел:</b>"
    )

def format_registration_date(dt: datetime):
    if not dt:
        return "—"
    MONTHS = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return f"{dt.day} {MONTHS[dt.month-1]} {dt.year}"

def reports_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu")]
    ])

async def main_menu(message: Message, user_id: int = None):
    if user_id is None:
        user_id = message.from_user.id if hasattr(message, "from_user") else None
    logging.info(f"[DEBUG USER_ID] main_menu: user_id={user_id}")

    access = await get_user_access(user_id)
    user_profile = await get_user_profile_info(user_id)
    now = datetime.utcnow()

    trial_active = (
            access and getattr(access, "trial_activated", False)
            and getattr(access, "trial_until", None)
            and access.trial_until and access.trial_until > now
    )
    paid_active = (
            access and access.paid_until and access.paid_until > now
    )

    # --- Исправленная обработка отсутствия подписки ---
    if not access or (not paid_active and not trial_active):
        trial_expired = (
                access and getattr(access, "trial_activated", False)
                and getattr(access, "trial_until", None)
                and access.trial_until and access.trial_until <= now
        )
        show_trial = not (access and getattr(access, "trial_activated", False))
        can_restore = False  # Можно доработать, если нужно

        await message.answer(
            "🔒 Для работы с ботом нужен доступ:\n"
            "— Пробный 1 день (один раз)\n"
            "— Или купить месяц за 399₽\n\n"
            "Если у вас был положительный баланс — нажмите «Восстановить доступ».",
            reply_markup=access_menu_keyboard(
                trial_active,
                trial_expired,
                show_trial=show_trial,
                can_restore=can_restore
            )
        )
        logging.info(f"[DEBUG USER_ID] Нет подписки! user_id={user_id}")
        return

    if paid_active:
        days_left = max((access.paid_until - now).days, 0)
        access_until = access.paid_until
    else:
        days_left = max((access.trial_until - now).days, 0)
        access_until = access.trial_until

    balance = days_left * 13
    seller_name = user_profile.seller_name if user_profile else "—"
    registration_date = getattr(user_profile, "created_at", None)

    text = format_user_info(seller_name, balance, days_left, access_until, registration_date)
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_inline_keyboard())

# ================== КОЛБЭКИ ДЛЯ ИНЛАЙН-КНОПОК ==================

@router.callback_query(F.data == "main_profile")
async def main_profile(callback: CallbackQuery, state: FSMContext):
    from bot.handlers.profile import profile_menu
    user_id = callback.from_user.id
    logging.info(f"[DEBUG USER_ID] main_profile callback: user_id={user_id}")
    await callback.message.delete()
    await profile_menu(callback.message, state)

@router.callback_query(F.data == "main_reports")
async def reports_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 <b>Раздел отчётов</b>\n\nЗдесь будут ваши отчёты.",
        reply_markup=reports_menu_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    logging.info(f"[DEBUG USER_ID] back_to_main_menu: user_id={user_id}")
    await callback.message.delete()
    await main_menu(callback.message, user_id=user_id)

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
