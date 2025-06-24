from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot.keyboards.keyboards import profile_keyboard
from storage.users import (
    get_user_access,
    set_user_api_key,
    get_user_api_key,
    remove_user_api_key,
    remove_user_account,
    get_user_profile_info,
    set_user_profile_info
)
from datetime import datetime
import aiohttp

router = Router()

class ProfileStates(StatesGroup):
    waiting_for_api_key = State()

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

async def ask_for_api_key(message: Message, state: FSMContext):
    await message.answer(
        "Пожалуйста, отправьте свой Wildberries API-ключ одним сообщением.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(ProfileStates.waiting_for_api_key)

async def profile_menu(message: Message):
    user_id = message.from_user.id
    access = await get_user_access(user_id)
    api_key = await get_user_api_key(user_id)
    user_profile = await get_user_profile_info(user_id)
    now = datetime.now()
    days_left = max((access.paid_until - now).days, 0) if access and access.paid_until else 0
    balance = days_left * 13
    seller_name = user_profile.seller_name if user_profile else "—"
    trade_mark = user_profile.trade_mark if user_profile else "—"
    paid_until = access.paid_until if access and access.paid_until else now

    text = format_user_info(seller_name, trade_mark, balance, days_left, paid_until)
    await message.answer(text, parse_mode="HTML", reply_markup=profile_keyboard(bool(api_key)))

@router.message(ProfileStates.waiting_for_api_key)
async def save_api_key(message: Message, state: FSMContext):
    from bot.handlers.main_menu import main_menu
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
                    "✅ API-ключ сохранён и проверен.\n\nВы возвращены в главное меню.",
                    reply_markup=ReplyKeyboardRemove()
                )
                await state.clear()
                await main_menu(message)
                return
            else:
                await message.answer(
                    "❌ Ключ невалиден. Попробуйте ввести другой ключ или нажмите 'Отмена'.",
                    reply_markup=profile_keyboard(False)
                )

@router.message(F.text == "Ввести API")
async def ask_api_btn(message: Message, state: FSMContext):
    await ask_for_api_key(message, state)

@router.message(F.text == "Удалить API")
async def del_api(message: Message):
    user_id = message.from_user.id
    await remove_user_api_key(user_id)
    await set_user_profile_info(user_id, None, None)
    await message.answer("API-ключ удалён.")
    await profile_menu(message)

@router.message(F.text == "Удалить пользователя")
async def del_account(message: Message):
    pro
    user_id = message.from_user.id
    await remove_user_account(user_id)
    await message.answer("Аккаунт удалён. Для повторной регистрации используйте /start.")

@router.message(F.text == "⬅️ Назад")
async def profile_back(message: Message):
    from bot.handlers.main_menu import main_menu
    await main_menu(message)
