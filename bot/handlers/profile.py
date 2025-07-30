from aiogram import Router, F
from aiogram.types import ReplyKeyboardRemove
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
    if not dt:
        return "—"
    return dt.strftime("%d.%m.%Y")

# Клавиатуры
def profile_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Заменить API-ключ", callback_data="replace_api")],
        [InlineKeyboardButton(text="🗑️ Удалить профиль", callback_data="delete_account")],
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
from storage.users import update_balance_on_access

async def profile_menu(message: Message, state: FSMContext = None, user_id: int = None):
    if user_id is None:
        user_id = message.from_user.id
    await update_balance_on_access(user_id)
    profile = await get_user_profile_info(user_id)
    access = await get_user_access(user_id)
    DAILY_COST = 399 // 30

    balance = getattr(access, "balance", 0)
    days_left = balance // DAILY_COST if balance >= 0 else 0
    registration_date = getattr(access, "created_at", None)
    reg_str = format_date(registration_date) if registration_date else "—"
    seller_name = getattr(profile, "seller_name", "—")

    text = (
        "👤 <b>Профиль</b>\n"
        "\n"
        f"🏪 <b>Магазин:</b> <code>{seller_name}</code>\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"💰 <b>Баланс:</b> <code>{balance}₽</code>\n"
        f"⏳ <b>Осталось дней:</b> <code>{days_left}</code>\n"
        f"🗓️ <b>Регистрация:</b> <code>{reg_str}</code>\n"
        "\n"
        "<b>🔑 Заменить API-ключ</b>\n<i>Если ключ устарел или истекает срок действия.</i>\n\n"
        "<b>🗑 Удалить профиль</b>\n<i>Если больше не планируете пользоваться ботом. Восстановление через поддержку.</i>"
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
            await message.answer(" ", reply_markup=ReplyKeyboardRemove())
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
    await cmd_start(callback.message, state)

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
