# bot/handlers/reports.py

"""
reports.py — хендлеры раздела отчётов MalinaWB.

Теперь ВСЕ функции отчётов доступны только пользователям с активным доступом (платный/пробный).
Если доступа нет — возвращается отказ.

Зависимости:
- reports_keyboard() из bot/keyboards/inline.py — формирует inline-кнопки меню отчётов.
- main_menu_keyboard(user_id) из bot/keyboards/main_menu.py.
- get_user_access() из storage.users — проверка доступа.

"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.keyboards.inline import reports_keyboard
from bot.keyboards.main_menu import main_menu_keyboard
from storage.users import get_user_access
from datetime import datetime

router = Router()

# --- Универсальная проверка доступа для отчётов ---
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

@router.message(Command("reports"))
async def reports_menu_msg(message: Message):
    if not await user_has_access(message.from_user.id):
        await message.answer("❌ Нет доступа к отчётам!\n\nАктивируйте пробный или платный доступ через /start.")
        return
    await message.answer(
        "📊 <b>Раздел отчётов</b>\n\nВыберите тип отчёта:",
        reply_markup=reports_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "📊 Отчёты")
async def reports_menu_reply_button(message: Message):
    if not await user_has_access(message.from_user.id):
        await message.answer("❌ Нет доступа к отчётам!\n\nАктивируйте пробный или платный доступ через /start.")
        return
    await message.answer(
        "📊 <b>Раздел отчётов</b>\n\nВыберите тип отчёта:",
        reply_markup=reports_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.in_([
    "remains_menu", "sales_menu", "ads_menu", "storage_entry", "profit_menu"
]))
async def reports_menu_cb(callback: CallbackQuery):
    if not await user_has_access(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        await callback.message.edit_text(
            "❌ Нет доступа к отчётам!\n\nАктивируйте пробный или платный доступ через /start."
        )
        return
    await callback.message.edit_text(
        "📊 <b>Раздел отчётов</b>\n\nВыберите тип отчёта:",
        reply_markup=reports_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "account_menu")
async def back_to_main_menu(callback: CallbackQuery):
    if not await user_has_access(callback.from_user.id):
        await callback.answer("Нет доступа!", show_alert=True)
        await callback.message.edit_text(
            "❌ Нет доступа!\n\nАктивируйте пробный или платный доступ через /start."
        )
        return
    await callback.message.delete()
    await callback.message.answer(
        "👋 Привет! Я MalinaWB v2 — твой бот для аналитики Wildberries!\n\n"
        "Я умею:\n"
        "— Показывать остатки\n"
        "— Строить отчёты по продажам\n"
        "— Готовить отчёты по хранению\n\n"
        "Воспользуйся меню или напиши /reports чтобы начать.",
        reply_markup=main_menu_keyboard(callback.from_user.id)
    )
    await callback.answer()
