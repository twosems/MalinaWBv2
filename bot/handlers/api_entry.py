from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from storage.users import (
    set_user_api_key, set_user_profile_info,
    update_user_id_by_seller_name
)
import aiohttp
import logging

router = Router()

class ApiEntryStates(StatesGroup):
    waiting_for_api_key = State()

class RestoreStates(StatesGroup):
    waiting_for_restore_api_key = State()
    confirm_restore_access = State()

# ======== ПРОБНЫЙ ДОСТУП ========
@router.callback_query(F.data == "trial")
async def activate_trial(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Введите ваш API-ключ для активации пробного доступа:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ApiEntryStates.waiting_for_api_key)


@router.message(ApiEntryStates.waiting_for_api_key)
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
                from storage.users import set_trial_access
                from datetime import datetime, timedelta
                now = datetime.utcnow()
                trial_period = timedelta(days=1)
                await set_trial_access(user_id, now + trial_period)
                await state.clear()
                from bot.handlers.main_menu import main_menu
                await message.answer(
                    "✅ Новый API-ключ сохранён и активирован пробный доступ.\n\nВы возвращены в главное меню.",
                    reply_markup=ReplyKeyboardRemove()
                )
                await main_menu(message, user_id=user_id)
            else:
                await message.answer("❌ Ключ невалиден. Попробуйте ввести другой ключ или нажмите /start.")

# ======== ВОССТАНОВЛЕНИЕ ДОСТУПА ========
@router.callback_query(F.data == "restore_account")
async def ask_restore_access(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введите <b>API-ключ магазина</b>, для которого хотите восстановить доступ:",
        parse_mode="HTML"
    )
    await state.set_state(RestoreStates.waiting_for_restore_api_key)


@router.message(RestoreStates.waiting_for_restore_api_key)
async def process_restore_api(message: Message, state: FSMContext):
    api_key = message.text.strip()
    user_id = message.from_user.id

    url = 'https://common-api.wildberries.ru/api/v1/seller-info'
    headers = {'Authorization': api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                await message.answer("❌ Ключ невалиден. Попробуйте снова или нажмите /start.")
                return
            data = await resp.json()
            seller_name = data.get('name')
            if not seller_name:
                await message.answer("Не удалось определить магазин по ключу.")
                return

    # !!! ВАЖНО: импортируй именно функцию поиска архивного!
    from storage.users import find_archived_user_by_seller_name
    archived = await find_archived_user_by_seller_name(seller_name)
    if not archived:
        await message.answer("Не найден архивный аккаунт с таким магазином. Попробуйте ещё раз или зарегистрируйтесь заново.")
        await state.clear()
        return

    await state.update_data(seller_name=seller_name, api_key=api_key)
    await message.answer(
        f"Обнаружен магазин <b>{seller_name}</b>.\n"
        "Восстановить доступ к этому магазину и привязать его к текущему Telegram аккаунту?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Восстановить", callback_data="do_restore_access")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_restore")]
            ]
        ),
        parse_mode="HTML"
    )
    await state.set_state(RestoreStates.confirm_restore_access)

@router.callback_query(F.data == "do_restore_access")
async def do_restore_access(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    seller_name = data.get("seller_name")
    api_key = data.get("api_key")
    user_id = callback.from_user.id

    await update_user_id_by_seller_name(seller_name, user_id)
    await set_user_api_key(user_id, api_key)
    await state.clear()
    await callback.message.edit_text("✅ Доступ восстановлён и привязан к вашему Telegram! Можете пользоваться ботом.")

    from bot.handlers.main_menu import main_menu
    await main_menu(callback.message, user_id=user_id)

@router.callback_query(F.data == "cancel_restore")
async def cancel_restore(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Восстановление отменено.")
