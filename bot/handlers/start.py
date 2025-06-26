from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from bot.keyboards.keyboards import guest_menu, access_menu_keyboard
from storage.users import get_user_access, create_user_access, set_trial_access, get_user_api_key

import logging  # Для логов

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

@router.callback_query(F.data == "guest_continue")
async def guest_continue(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    access = await get_user_access(user_id)
    now = datetime.utcnow()

    # --- ОТЛАДКА: Выводим состояние access ---
    logging.info(f"[DEBUG access] {access.__dict__ if access else None}")
    if access:
        logging.info(
            f"[DEBUG fields] user_id={user_id} "
            f"trial_activated={access.trial_activated}, trial_until={access.trial_until}, paid_until={access.paid_until}"
        )
        # Выводим отладочную информацию пользователю — удали после анализа!
        await callback.message.answer(
            f"<b>DEBUG:</b>\n"
            f"trial_activated: <code>{access.trial_activated}</code>\n"
            f"trial_until: <code>{access.trial_until}</code>\n"
            f"paid_until: <code>{access.paid_until}</code>",
            parse_mode="HTML"
        )

    # Если записи нет — создаём
    if not access:
        await create_user_access(user_id)
        access = await get_user_access(user_id)

    api_key = await get_user_api_key(user_id)

    # --- Проверка активного доступа ---
    trial_active = (
            access
            and bool(access.trial_activated)
            and access.trial_until
            and access.trial_until > now
    )
    paid_active = (
            access
            and access.paid_until
            and access.paid_until > now
    )

    if trial_active or paid_active:
        if not api_key:
            from bot.handlers.profile import ask_for_api_key
            await callback.message.delete()
            await ask_for_api_key(callback.message, state)
            return
        else:
            from bot.handlers.main_menu import main_menu
            await callback.message.delete()
            await main_menu(callback.message)
            return

    # --- Если сюда попали — нет доступа ---
    trial_expired = (
            access
            and bool(access.trial_activated)
            and access.trial_until
            and access.trial_until <= now
    )
    show_trial = not (access and access.trial_activated)

    await callback.message.delete()
    await callback.message.answer(
        "🔒 Для работы с ботом нужен доступ:\n"
        "— Пробный 1 день (один раз)\n"
        "— Или купить месяц за 399₽\n\n"
        "Выберите вариант ниже:",
        reply_markup=access_menu_keyboard(trial_active, trial_expired, show_trial=show_trial)
    )

@router.callback_query(F.data == "trial")
async def activate_trial(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    now = datetime.utcnow()
    trial_period = timedelta(days=1)  # пробный доступ на 1 день
    await set_trial_access(user_id, now + trial_period)
    await callback.message.delete()
    await callback.answer()
    from bot.handlers.profile import ask_for_api_key
    await ask_for_api_key(callback.message, state)

@router.callback_query(F.data == "buy")
async def buy_access(callback: CallbackQuery):
    await callback.answer(
        "💳 Оплата пока не реализована.\nПопросите администратора выдать доступ вручную.",
        show_alert=True
    )

@router.callback_query(F.data == "trial_disabled")
async def trial_disabled(callback: CallbackQuery):
    await callback.answer("Пробный доступ уже был активирован.", show_alert=True)

@router.callback_query(F.data == "back_to_greeting")
async def back_to_greeting(callback: CallbackQuery):
    await callback.message.delete()
    await cmd_start(callback.message)
    await callback.answer()
