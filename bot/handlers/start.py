from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from bot.keyboards.keyboards import guest_menu, access_menu_keyboard
from storage.users import get_user_access, create_user_access, set_trial_access, get_user_api_key

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "🤖 <b>MalinaWB — ваш личный ассистент на Wildberries!</b>\n\n"
        "🔹 <b>Автоматизация отчётов</b> — получайте актуальные данные без лишних движений\n"
        "🔹 <b>Аналитика и уведомления</b> — всегда держите руку на пульсе бизнеса\n"
        "🔹 <b>Упрощение рутины</b> — экономьте время на важном!\n\n"
        "Нажмите <b>Продолжить</b>, чтобы зарегистрироваться и открыть доступ к возможностям бота 👇",
        reply_markup=guest_menu(),
        parse_mode="HTML"
    )

@router.message(F.text == "Продолжить")
async def guest_continue(message: Message, state: FSMContext):
    user_id = message.from_user.id
    access = await get_user_access(user_id)
    now = datetime.now()
    if not access:
        await create_user_access(user_id)
        access = await get_user_access(user_id)

    api_key = await get_user_api_key(user_id)

    if (
            access and (
            (access.paid_until and access.paid_until > now)
            or (access.trial_activated and access.trial_until and access.trial_until > now)
    )
    ):
        if not api_key:
            from bot.handlers.profile import ask_for_api_key
            await ask_for_api_key(message, state)
            await message.reply("", reply_markup=ReplyKeyboardRemove())
            return
        else:
            from bot.handlers.main_menu import main_menu
            await main_menu(message)
            await message.reply("", reply_markup=ReplyKeyboardRemove())
            return

    trial_expired = access.trial_activated and access.trial_until and access.trial_until <= now
    trial_active = access.trial_activated and access.trial_until and access.trial_until > now
    show_trial = not access.trial_activated

    await message.answer(
        "🔒 Для работы с ботом нужен доступ:\n"
        "— Пробный 1 час (один раз)\n"
        "— Или купить месяц за 399₽\n\n"
        "Выберите вариант ниже:",
        reply_markup=access_menu_keyboard(trial_active, trial_expired, show_trial=show_trial)
    )
    await message.reply("", reply_markup=ReplyKeyboardRemove())

@router.callback_query(F.data == "trial")
async def activate_trial(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    now = datetime.now()
    await set_trial_access(user_id, now + timedelta(hours=1))
    await callback.message.delete()
    await callback.answer()
    from bot.handlers.profile import ask_for_api_key
    await ask_for_api_key(callback.message, state)

@router.callback_query(F.data == "buy")
async def buy_access(callback: CallbackQuery):
    await callback.answer("💳 Оплата пока не реализована.\nПопросите администратора выдать доступ вручную.", show_alert=True)

@router.callback_query(F.data == "trial_disabled")
async def trial_disabled(callback: CallbackQuery):
    await callback.answer("Пробный доступ уже был активирован.", show_alert=True)

@router.callback_query(F.data == "back_to_greeting")
async def back_to_greeting(callback: CallbackQuery):
    await callback.message.delete()
    await cmd_start(callback.message)
    await callback.answer()
