from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from datetime import datetime, timedelta

from bot.keyboards.main_menu import main_menu_keyboard

from storage.users import (
    get_user_access,
    create_user_access,
    set_trial_access,
    get_user_api_key
)
from bot.handlers.profile import profile_menu

router = Router()

def guest_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Продолжить")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Нажмите 'Продолжить', чтобы начать"
    )

def access_menu_keyboard(trial_active=False, trial_expired=False, show_trial=True) -> InlineKeyboardMarkup:
    kb = []
    if show_trial:
        if not trial_active and not trial_expired:
            kb.append([InlineKeyboardButton(text="🕒 Пробный доступ (1 час)", callback_data="trial")])
        else:
            label = "🕒 Пробный доступ (уже активирован)" if trial_expired else "🕒 Пробный доступ (активен)"
            kb.append([InlineKeyboardButton(text=label, callback_data="trial_disabled")])
    kb.append([InlineKeyboardButton(text="💳 Оплатить доступ 399₽/мес", callback_data="buy")])
    kb.append([InlineKeyboardButton(text="🆘 Техподдержка", callback_data="support")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_greeting")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def profile_menu_keyboard():
    # Временное меню для профиля неавторизованного
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Оплатить")],
            [KeyboardButton(text="Ввести API")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )

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
async def guest_continue(message: Message):
    user_id = message.from_user.id
    access = await get_user_access(user_id)
    now = datetime.now()
    if not access:
        await create_user_access(user_id)
        access = await get_user_access(user_id)
    if (
            access and (
            (access.paid_until and access.paid_until > now)
            or (access.trial_activated and access.trial_until and access.trial_until > now)
    )
    ):
        # ВСЕГДА предлагаем ввести API, если доступа ещё не было, или api отсутствует
        await profile_menu(message, use_main_menu=False, prompt_api_if_none=True)
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

@router.message(F.text == "Оплатить")
async def pay_from_profile(message: Message):
    user_id = message.from_user.id
    access = await get_user_access(user_id)
    now = datetime.now()
    trial_expired = access and access.trial_activated and access.trial_until and access.trial_until <= now
    trial_active = access and access.trial_activated and access.trial_until and access.trial_until > now
    await message.answer(
        "💳 Для работы с ботом нужен платный доступ:\n\n"
        "— Купите месяц за 399₽\n\n"
        "Выберите вариант ниже:",
        reply_markup=access_menu_keyboard(trial_active, trial_expired, show_trial=False)
    )

@router.callback_query(F.data == "trial")
async def activate_trial(callback: CallbackQuery):
    user_id = callback.from_user.id
    now = datetime.now()
    await set_trial_access(user_id, now + timedelta(hours=1))
    await callback.message.delete()
    await callback.answer()
    # ВСЕГДА предлагаем ввести API, сразу после активации trial
    await profile_menu(callback.message, use_main_menu=False, prompt_api_if_none=True)

@router.callback_query(F.data == "buy")
async def buy_access(callback: CallbackQuery):
    await callback.answer("💳 Оплата пока не реализована.\nПопросите администратора выдать доступ вручную.", show_alert=True)

@router.callback_query(F.data == "support")
async def support_access(callback: CallbackQuery):
    await callback.answer("🆘 Техподдержка: @your_support_username", show_alert=True)

@router.callback_query(F.data == "trial_disabled")
async def trial_disabled(callback: CallbackQuery):
    await callback.answer("Пробный доступ уже был активирован.", show_alert=True)

@router.callback_query(F.data == "back_to_greeting")
async def back_to_greeting(callback: CallbackQuery):
    await callback.message.edit_text(
        "🤖 <b>MalinaWB — ваш личный ассистент на Wildberries!</b>\n\n"
        "🔹 <b>Автоматизация отчётов</b> — получайте актуальные данные без лишних движений\n"
        "🔹 <b>Аналитика и уведомления</b> — всегда держите руку на пульсе бизнеса\n"
        "🔹 <b>Упрощение рутины</b> — экономьте время на важном!\n\n"
        "Нажмите <b>Продолжить</b>, чтобы зарегистрироваться и открыть доступ к возможностям бота 👇",
        reply_markup=guest_menu(),
        parse_mode="HTML"
    )
    await callback.answer()
