from aiogram import Router, F
from aiogram.types import Message
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
import aiohttp

router = Router()

class ProfileStates(StatesGroup):
    waiting_for_api_key = State()

async def profile_menu(message: Message):
    user_id = message.from_user.id
    access = await get_user_access(user_id)
    api_key = await get_user_api_key(user_id)
    user_profile = await get_user_profile_info(user_id)
    seller_name = user_profile.seller_name if user_profile else "—"
    trade_mark = user_profile.trade_mark if user_profile else "—"
    await message.answer(
        f"👤 <b>Профиль (настройки)</b>\n"
        f"Магазин: <b>{seller_name}</b>\nБренд: <b>{trade_mark}</b>\n",
        parse_mode="HTML",
        reply_markup=profile_keyboard()
    )

@router.message(F.text == "Ввести API")
async def ask_for_api_key(message: Message, state: FSMContext):
    await message.answer(
        "Пожалуйста, отправьте свой Wildberries API-ключ одним сообщением.",
        reply_markup=profile_keyboard()
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
                await message.answer("✅ API-ключ сохранён и проверен.", reply_markup=profile_keyboard())
                await state.clear()
                await profile_menu(message)
                return
            else:
                await message.answer("❌ Ключ невалиден. Попробуйте ещё раз или нажмите 'Назад'.", reply_markup=profile_keyboard())

@router.message(F.text == "Удалить API")
async def del_api(message: Message):
    user_id = message.from_user.id
    await remove_user_api_key(user_id)
    await set_user_profile_info(user_id, None, None)
    await message.answer("API-ключ удалён.", reply_markup=profile_keyboard())
    await profile_menu(message)

@router.message(F.text == "Удалить аккаунт")
async def del_account(message: Message):
    user_id = message.from_user.id
    await remove_user_account(user_id)
    await message.answer("Аккаунт удалён. Для повторной регистрации используйте /start.")

@router.message(F.text == "⬅️ Назад")
async def profile_back(message: Message):
    from bot.handlers.main_menu import main_menu
    await main_menu(message)
