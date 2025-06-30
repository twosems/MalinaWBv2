from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from storage.users import (
    get_user_access,
    get_user_api_key,
    set_user_api_key,
    remove_user_api_key,
    get_user_profile_info,
    set_user_profile_info,
    remove_user_account
)
import aiohttp
from datetime import datetime

router = Router()

class ProfileStates(StatesGroup):
    waiting_for_new_api_key = State()
    waiting_for_api_key_confirm = State()
    waiting_for_account_delete_confirm = State()

# Форматирование даты для красивого отображения
MONTHS = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]
def format_date(dt: datetime):
    return f"{dt.day} {MONTHS[dt.month-1]} {dt.year}"

# Клавиатуры
def profile_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Заменить API-ключ", callback_data="replace_api")],
        [InlineKeyboardButton(text="🗑️ Удалить аккаунт", callback_data="delete_account")],
        [InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="back_to_main_menu")]
    ])

def api_change_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ ОК", callback_data="confirm_api_change")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_api_change")]
    ])

def confirm_delete_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="confirm_account_delete")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_account_delete")]
    ])

# Главное меню профиля
async def profile_menu(message: Message, state: FSMContext = None):
    user_id = message.from_user.id
    profile = await get_user_profile_info(user_id)
    access = await get_user_access(user_id)
    now = datetime.utcnow()
    paid_until = getattr(access, "paid_until", None)
    trial_until = getattr(access, "trial_until", None)
    registration_date = getattr(profile, "registration_date", None)
    days_left = 0

    # Дата окончания доступа
    if paid_until and paid_until > now:
        days_left = (paid_until - now).days
        access_until = paid_until
    elif trial_until and trial_until > now:
        days_left = (trial_until - now).days
        access_until = trial_until
    else:
        access_until = paid_until or trial_until or now

    balance = days_left * 13

    reg_str = format_date(registration_date) if registration_date else "—"

    text = (
        f"👤 <b>Профиль пользователя</b>\n"
        f"🛍️ <b>Магазин:</b> {getattr(profile, 'seller_name', '—')}\n"
        f"💰 <b>Баланс:</b> <code>{balance}₽</code>\n"
        f"⏳ <b>Осталось дней:</b> <code>{days_left}</code>\n"
        f"📅 <b>Подписка до:</b> <code>{format_date(access_until)}</code>\n"
        f"📆 <b>Зарегистрирован:</b> <code>{reg_str}</code>\n"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=profile_inline_keyboard())
    if state:
        await state.clear()

# --- Кнопка "Заменить API-ключ" ---
@router.callback_query(F.data == "replace_api")
async def replace_api(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите новый API-ключ для текущего магазина одним сообщением.\n\n"
        "После ввода появятся кнопки для подтверждения или отмены.",
        reply_markup=None
    )
    await state.set_state(ProfileStates.waiting_for_new_api_key)

# --- Вводим новый API-ключ ---
@router.message(ProfileStates.waiting_for_new_api_key)
async def input_new_api_key(message: Message, state: FSMContext):
    new_api_key = message.text.strip()
    url = 'https://common-api.wildberries.ru/api/v1/seller-info'
    headers = {'Authorization': new_api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                await message.answer("❌ Ключ невалиден, попробуйте другой ключ.")
                return
            data = await resp.json()
            seller_name = data.get('name', '—')
            user_id = message.from_user.id
            profile = await get_user_profile_info(user_id)
            if seller_name != getattr(profile, "seller_name", None):
                await message.answer("❌ Ключ не соответствует вашему магазину. Добавьте ключ от текущего магазина.")
                return
            await state.update_data(new_api_key=new_api_key)
            await message.answer(
                f"✅ Новый ключ для магазина <b>{seller_name}</b>.\n\nПодтвердить замену?",
                parse_mode="HTML",
                reply_markup=api_change_keyboard()
            )
            await state.set_state(ProfileStates.waiting_for_api_key_confirm)

# --- Кнопка "ОК" (подтверждение смены ключа) ---
@router.callback_query(ProfileStates.waiting_for_api_key_confirm, F.data == "confirm_api_change")
async def confirm_api_change(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    new_api_key = data.get("new_api_key")
    user_id = callback.from_user.id
    await set_user_api_key(user_id, new_api_key)
    await callback.message.edit_text(
        "✅ Новый API-ключ сохранён и авторизован.",
        reply_markup=None
    )
    await state.clear()
    await profile_menu(callback.message, state)

# --- Кнопка "Отмена" (отмена смены ключа) ---
@router.callback_query(ProfileStates.waiting_for_api_key_confirm, F.data == "cancel_api_change")
async def cancel_api_change(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Замена API-ключа отменена.", reply_markup=None)
    await state.clear()
    await profile_menu(callback.message, state)

# --- Кнопка "Удалить аккаунт" ---
@router.callback_query(F.data == "delete_account")
async def delete_account_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Вы уверены, что хотите удалить аккаунт?\n\n"
        "Баланс и дата регистрации будут сохранены для будущей регистрации.",
        reply_markup=confirm_delete_keyboard()
    )
    await state.set_state(ProfileStates.waiting_for_account_delete_confirm)

# --- Подтвердить удаление аккаунта ---
@router.callback_query(ProfileStates.waiting_for_account_delete_confirm, F.data == "confirm_account_delete")
async def confirm_account_delete(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await remove_user_api_key(user_id)
    await remove_user_account(user_id)
    await callback.message.edit_text(
        "Профиль удалён.\n\nДанные об оплате и регистрации сохранены.\n\nДля новой регистрации используйте /start.",
        reply_markup=None
    )
    await state.clear()
    from bot.handlers.start import cmd_start
    await cmd_start(callback.message)

# --- Отмена удаления аккаунта ---
@router.callback_query(ProfileStates.waiting_for_account_delete_confirm, F.data == "cancel_account_delete")
async def cancel_account_delete(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Удаление аккаунта отменено.", reply_markup=None)
    await state.clear()
    await profile_menu(callback.message, state)

# --- Кнопка "Назад в главное меню" ---
@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    from bot.handlers.main_menu import main_menu
    await callback.message.delete()
    await main_menu(callback.message, user_id=callback.from_user.id)
    if state:
        await state.clear()
