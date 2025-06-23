from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
import aiohttp

from storage.users import (
    get_user_access,
    set_user_api_key,
    get_user_api_key,
    remove_user_api_key,
    remove_user_account,
    get_user_profile_info,
    set_user_profile_info
)
from bot.keyboards.main_menu import main_menu_keyboard

router = Router()

class ProfileStates(StatesGroup):
    waiting_for_api_key = State()

def profile_new_user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ввести API")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )

def profile_full_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Удалить API")],
            [KeyboardButton(text="Удалить аккаунт")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )

def profile_api_fail_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True
    )

async def user_has_access(user_id: int):
    access = await get_user_access(user_id)
    if not access:
        return False
    now = datetime.now()
    if access.paid_until and access.paid_until > now:
        return True
    if access.trial_activated and access.trial_until and access.trial_until > now:
        return True
    return False

def format_date(date: datetime):
    MONTHS = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return f"{date.day} {MONTHS[date.month-1]} {date.year}"

@router.message(F.text == "👤 Профиль")
async def profile_menu(message: Message, use_main_menu=False, prompt_api_if_none=False):
    user_id = message.from_user.id
    if not await user_has_access(user_id):
        await message.answer("❌ Нет доступа!\n\nАктивируйте пробный или платный доступ через /start.")
        return

    access = await get_user_access(user_id)
    api_key = await get_user_api_key(user_id)
    user_profile = await get_user_profile_info(user_id)
    now = datetime.now()

    if not api_key or prompt_api_if_none:
        await message.answer(
            "🔑 <b>Для получения доступа к функциям MalinaWB введите ваш ключ API.</b>",
            reply_markup=profile_new_user_keyboard(),
            parse_mode="HTML"
        )
        return

    if access.paid_until and access.paid_until > now:
        days_left = (access.paid_until - now).days
        balance = int(days_left * 399 / 30)
        access_type = f"💰 Баланс: <b>{balance} руб.</b>\n⏳ Дней доступа: <b>{days_left}</b>"
        sub_msg = f"📅 Подписка до: <b>{format_date(access.paid_until)}</b>"
    elif access.trial_activated and access.trial_until and access.trial_until > now:
        minutes_left = int((access.trial_until - now).total_seconds() // 60)
        access_type = f"🕒 Пробный доступ\n⏳ Минут осталось: <b>{minutes_left}</b>"
        sub_msg = f"Пробный до: <b>{format_date(access.trial_until)}</b>"
    else:
        access_type = "💰 Баланс: <b>0 руб.</b>\n⏳ Дней доступа: <b>0</b>"
        sub_msg = "Нет активной подписки"

    seller_name = user_profile.seller_name if user_profile else "—"
    trade_mark = user_profile.trade_mark if user_profile else "—"

    if use_main_menu:
        reply_kb = main_menu_keyboard()
    else:
        reply_kb = profile_full_keyboard() if api_key else profile_new_user_keyboard()

    await message.answer(
        f"👤 <b>Ваш профиль</b>\n\n"
        f"{access_type}\n\n"
        f"🛍️ Магазин: <b>{seller_name}</b>\n"
        f"🏷️ Бренд: <b>{trade_mark}</b>\n\n"
        f"{sub_msg}",
        parse_mode="HTML",
        reply_markup=reply_kb
    )

@router.message(F.text == "Ввести API")
async def ask_for_api_key(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await user_has_access(user_id):
        await message.answer("❌ Нет доступа!\n\nАктивируйте пробный или платный доступ через /start.")
        return
    await message.answer(
        "Пожалуйста, отправьте свой Wildberries API-ключ одним сообщением.",
        reply_markup=profile_api_fail_keyboard()
    )
    await state.set_state(ProfileStates.waiting_for_api_key)

@router.message(ProfileStates.waiting_for_api_key)
async def save_api_key(message: Message, state: FSMContext):
    user_id = message.from_user.id
    api_key = message.text.strip()
    url = 'https://common-api.wildberries.ru/api/v1/seller-info'
    headers = {'Authorization': api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                seller_name = data.get('name', '—')
                trade_mark = data.get('tradeMark', '—')
                await set_user_api_key(user_id, api_key)
                await set_user_profile_info(user_id, seller_name, trade_mark)
                await message.answer(
                    "✅ API-ключ сохранён и проверен.\n\nПрофиль обновлён.",
                    reply_markup=main_menu_keyboard()
                )
                await state.clear()
                await profile_menu(message, use_main_menu=True)
                return
            else:
                await message.answer(
                    "❌ Ключ невалиден. Попробуйте ввести другой ключ или нажмите 'Отмена'.",
                    reply_markup=profile_api_fail_keyboard()
                )

@router.message(F.text == "Отмена")
async def api_cancel(message: Message, state: FSMContext):
    await state.clear()
    await profile_menu(message, prompt_api_if_none=True)

@router.message(F.text == "Удалить API")
async def del_api(message: Message):
    user_id = message.from_user.id
    await remove_user_api_key(user_id)
    await set_user_profile_info(user_id, None, None)
    await message.answer("API-ключ удалён.", reply_markup=profile_new_user_keyboard())
    await profile_menu(message, prompt_api_if_none=True)

@router.message(F.text == "Удалить аккаунт")
async def del_account(message: Message):
    user_id = message.from_user.id
    await remove_user_account(user_id)
    await message.answer("Аккаунт удалён. Для повторной регистрации используйте /start.")

@router.message(F.text == "⬅️ Назад")
async def profile_back(message: Message):
    from bot.handlers.start import cmd_start
    await cmd_start(message)
