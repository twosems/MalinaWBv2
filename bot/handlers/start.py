import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from bot.keyboards.keyboards import guest_menu, access_menu_keyboard
from storage.users import (
    get_user_access, create_user_access, set_trial_access, get_user_api_key,
    find_user_by_seller_name, find_archived_user_by_seller_name, update_user_id_by_seller_name
)

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    logging.info(f"[DEBUG USER_ID] /start: user_id={message.from_user.id}")
    await state.clear()
    await message.answer(
        "🤖 <b>MalinaWB — ваш личный ассистент на Wildberries!</b>\n\n"
        "🔹 <b>Автоматизация отчётов</b>\n"
        "🔹 <b>Аналитика и уведомления</b>\n"
        "🔹 <b>Упрощение рутины</b>\n\n"
        "Нажмите <b>Продолжить</b>, чтобы зарегистрироваться и открыть доступ к возможностям бота 👇",
        reply_markup=guest_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "guest_continue")
async def guest_continue(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    now = datetime.utcnow()
    access = await get_user_access(user_id)

    menu_type = None
    trial_active = False
    paid_active = False
    has_balance = False

    if access:
        is_archived = getattr(access, "is_archived", False)
        trial_active = access.trial_until and access.trial_until > now
        paid_active = access.paid_until and access.paid_until > now
        has_balance = paid_active or trial_active

        # 1. Активный аккаунт с подпиской — сразу в основное меню
        if not is_archived and (paid_active or trial_active):
            from bot.handlers.main_menu import main_menu
            await callback.message.delete()
            await main_menu(callback.message, user_id=user_id)
            return

        # 2. Архивный аккаунт
        if is_archived:
            if has_balance:
                menu_type = "restore"
            else:
                menu_type = "only_pay"
        # 3. Активный аккаунт без баланса
        else:
            menu_type = "only_pay" if not has_balance else "restore"
    else:
        # 4. Новый пользователь
        await create_user_access(user_id)
        menu_type = "new"

    await callback.message.delete()
    if menu_type == "new":
        await callback.message.answer(
            "🔒 Для работы с ботом нужен доступ:\n"
            "— Пробный 1 день (один раз)\n"
            "— Или купить месяц за 399₽\n",
            reply_markup=access_menu_keyboard(show_trial=True, can_restore=False)
        )
    elif menu_type == "restore":
        await callback.message.answer(
            "🔒 У вас есть положительный баланс — восстановите доступ или оплатите.",
            reply_markup=access_menu_keyboard(show_trial=False, can_restore=True)
        )
    elif menu_type == "only_pay":
        await callback.message.answer(
            "🔒 Для работы с ботом нужен доступ. Пробный период недоступен, оплатите доступ.",
            reply_markup=access_menu_keyboard(show_trial=False, can_restore=False)
        )

# ---------- ОБРАБОТЧИКИ ДЛЯ КНОПОК В МЕНЮ ДОСТУПА ----------

@router.callback_query(F.data == "trial")
async def activate_trial(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    logging.info(f"[DEBUG USER_ID] activate_trial: user_id={user_id}")
    now = datetime.utcnow()
    trial_period = timedelta(days=1)
    await set_trial_access(user_id, now + trial_period)
    await callback.message.delete()
    # Переходим к вводу API-ключа


@router.callback_query(F.data == "restore_account")
async def restore_account(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    from bot.handlers.api_entry import ask_restore_access
    await ask_restore_access(callback, state)


@router.callback_query(F.data == "buy")
async def buy_access(callback: CallbackQuery):
    await callback.answer(
        "💳 Оплата пока не реализована.\nПопросите администратора выдать доступ вручную.",
        show_alert=True
    )

@router.callback_query(F.data == "back_to_greeting")
async def back_to_greeting(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await cmd_start(callback.message, state)
    await callback.answer()
