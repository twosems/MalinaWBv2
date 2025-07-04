"""
handlers/main_menu.py

Главное меню пользователя.

- Проверяет актуальность доступа (баланс или активный триал) — если доступа нет, отправляет пользователя к /start.
- Показывает основную информацию: магазин, баланс, остаток дней, дату регистрации.
- Навигация по разделам (профиль, отчёты, аналитика и др.) через инлайн-кнопки.

Использует:
    - get_user_access, has_active_access — проверка доступа
    - get_user_profile_info — получение профиля
    - main_menu_inline_keyboard — кнопки основного меню
    - access_menu_keyboard — меню оплаты/пробного доступа
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.keyboards import main_menu_inline_keyboard
from storage.users import get_user_access, get_user_profile_info, has_active_access
from datetime import datetime
from aiogram.fsm.context import FSMContext
import logging

router = Router()

def format_registration_date(dt: datetime):
    if not dt:
        return "—"
    MONTHS = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return f"{dt.day} {MONTHS[dt.month-1]} {dt.year}"

async def main_menu(message: Message, user_id: int = None):
    """
    Главное меню.
    - Если активен пробный доступ — блок с баланса и днями заменён на прочерки, а инфо о триале вынесено отдельным абзацем ниже.
    - Если триал не активен — обычный вывод баланса и дней, без инфо о триале.
    """
    if user_id is None:
        user_id = message.from_user.id if hasattr(message, "from_user") else None
    logging.info(f"[DEBUG USER_ID] main_menu: user_id={user_id}")

    access = await get_user_access(user_id)
    if not access or not has_active_access(access):
        await message.answer(
            "⛔️ Ваш доступ неактивен или истёк.\n"
            "Пожалуйста, начните с команды /start.",
        )
        return

    user_profile = await get_user_profile_info(user_id)
    DAILY_COST = 399 // 30

    trial_activated = getattr(access, "trial_activated", False)
    trial_until = getattr(access, "trial_until", None)
    now = datetime.utcnow()
    in_trial = trial_activated and trial_until and now <= trial_until

    seller_name = user_profile.seller_name if user_profile else "—"
    registration_date = getattr(access, "created_at", None)

    if in_trial:
        # Показываем прочерки и отдельный блок о пробнике
        balance_block = (
            f"💰 <b>Баланс:</b> <code>—</code>\n"
            f"⏳ <b>Осталось дней:</b> <code>—</code>\n"
        )
        trial_info = (
            f"\n🆓 <b>Пробный доступ активен</b>\n"
            f"⏳ <b>Действует до:</b> <code>{trial_until.strftime('%d.%m.%Y %H:%M')}</code>\n"
        )
    else:
        balance = getattr(access, "balance", 0)
        days_left = balance // DAILY_COST if balance > 0 else 0
        balance_block = (
            f"💰 <b>Баланс:</b> <code>{balance}₽</code>\n"
            f"⏳ <b>Осталось дней:</b> <code>{days_left}</code>\n"
        )
        trial_info = ""

    text = (
        f"👤 <b>Основное Меню</b>\n"
        f"🛍️ <b>Магазин:</b> {seller_name}\n"
        f"{balance_block}"
        f"{trial_info}"
        f"{f'🗓️ <b>Зарегистрирован:</b> <code>{format_registration_date(registration_date)}</code>' if registration_date else ''}\n"
        f"\n<b>Выберите раздел:</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_inline_keyboard())

# Остальные хендлеры (разделы меню) — без изменений, только нужное оставляй
@router.callback_query(F.data == "main_profile")
async def main_profile(callback: CallbackQuery, state: FSMContext):
    from bot.handlers.profile import profile_menu
    user_id = callback.from_user.id
    await callback.message.delete()
    await profile_menu(callback.message, state, user_id=user_id)

@router.callback_query(F.data == "main_reports")
async def reports_menu(callback: CallbackQuery):
    # Тут можно поменять на reports_keyboard, если хочешь сразу выводить меню отчётов
    await callback.message.edit_text(
        "📊 <b>Раздел отчётов</b>\n\nЗдесь будут ваши отчёты.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu")]]
        ),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
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
