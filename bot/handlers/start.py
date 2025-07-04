"""
bot/handlers/start.py

Стартовые обработчики:
- /start и "Продолжить" для входа в бота
- Проверка и актуализация доступа пользователя
- Списание баланса только за реально оплаченные дни (баланс не уходит в минус)
- Меню получения доступа: пробный период, оплата, восстановление
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from bot.keyboards.keyboards import blocked_menu_keyboard
from bot.keyboards.keyboards import guest_menu, access_menu_keyboard

from storage.users import (
    get_user_access, create_user_access, set_trial_access, get_user_api_key,
    find_user_by_seller_name, find_archived_user_by_seller_name, update_user_id_by_seller_name,
    update_balance_on_access,
    has_active_access
)

# --- Импорты для глобального кэша складов ---
from storage.warehouses import need_update_warehouses_cache, cache_warehouses
from bot.services.wildberries_api import fetch_warehouses_from_api




router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    logging.info(f"[DEBUG USER_ID] /start: user_id={message.from_user.id}")
    await state.clear()
    user_id = message.from_user.id

    # Актуализируем баланс (списываем только за оплаченные дни, минуса не бывает)
    await update_balance_on_access(user_id)

    # ----------- ГЛОБАЛЬНОЕ КЕШИРОВАНИЕ СКЛАДОВ -----------
    try:
        if await need_update_warehouses_cache():
            api_key = await get_user_api_key(user_id)
            if api_key:
                warehouses = await fetch_warehouses_from_api(api_key)
                if warehouses:
                    await cache_warehouses(warehouses, updated_by=user_id)
                    logging.info(f"[WAREHOUSES] Глобальный список складов обновлён пользователем {user_id}")
                else:
                    logging.warning(f"[WAREHOUSES] Не удалось получить список складов через API (user_id={user_id})")
            else:
                logging.warning(f"[WAREHOUSES] Нет API-ключа у пользователя {user_id}, пропуск обновления кэша")
        else:
            logging.info("[WAREHOUSES] Кэш складов актуален, обновление не требуется")
    except Exception as e:
        logging.error(f"[WAREHOUSES] Ошибка при обновлении складов: {e}")
    # -----------------------------------------------------

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

    await update_balance_on_access(user_id)
    access = await get_user_access(user_id)
    now = datetime.utcnow()

    is_archived = getattr(access, "is_archived", False) if access else False
    balance = getattr(access, "balance", 0) if access else 0
    trial_activated = getattr(access, "trial_activated", False) if access else False
    trial_until = getattr(access, "trial_until", None) if access else None
    in_trial = trial_activated and trial_until and now <= trial_until
    trial_expired = (not in_trial) and (trial_activated or trial_until)

    # Основной сценарий доступа
    if access and not is_archived and (balance > 0 or in_trial):
        from bot.handlers.main_menu import main_menu
        await callback.message.delete()
        await main_menu(callback.message, user_id=user_id)
        return

    menu_type = None

    if access:
        if is_archived:
            menu_type = "restore" if balance > 0 else "only_pay"
        elif in_trial:
            menu_type = None
        elif balance == 0 and not in_trial and not is_archived:
            # ВАЖНО: пользователь был платным, триал не активен, баланс кончился
            menu_type = "blocked"
        elif trial_expired:
            menu_type = "trial_expired"
        else:
            menu_type = "only_pay"
    else:
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
    elif menu_type == "trial_expired":
        await callback.message.answer(
            "🕒 <b>Пробный доступ завершён.</b>\n\n"
            "Для продолжения работы с ботом оплатите доступ.",
            reply_markup=access_menu_keyboard(show_trial=False, can_restore=False),
            parse_mode="HTML"
        )
    elif menu_type == "blocked":
        await callback.message.answer(
            "⛔ <b>Ваш доступ временно приостановлен.</b>\n\n"
            "Баланс исчерпан. Для продолжения работы с ботом пополните баланс.",
            reply_markup=blocked_menu_keyboard(),
            parse_mode="HTML"
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
