# bot/handlers/reports.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.keyboards.inline import reports_keyboard

router = Router()

@router.message(Command("reports"))
async def reports_menu_msg(message: Message):
    await message.answer(
        "📊 <b>Раздел отчётов</b>\n\nВыберите тип отчёта:",
        reply_markup=reports_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "📊 Отчёты")
async def reports_menu_reply_button(message: Message):
    await message.answer(
        "📊 <b>Раздел отчётов</b>\n\nВыберите тип отчёта:",
        reply_markup=reports_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.in_([
    "remains_menu", "sales_menu", "ads_menu", "storage_entry", "profit_menu"
]))
async def reports_menu_cb(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 <b>Раздел отчётов</b>\n\nВыберите тип отчёта:",
        reply_markup=reports_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "account_menu")
async def back_to_main_menu(callback: CallbackQuery):
    from bot.handlers.start import main_menu_keyboard
    await callback.message.delete()
    await callback.message.answer(
        "👋 Привет! Я MalinaWB v2 — твой бот для аналитики Wildberries!\n\n"
        "Я умею:\n"
        "— Показывать остатки\n"
        "— Строить отчёты по продажам\n"
        "— Готовить отчёты по хранению\n\n"
        "Воспользуйся меню или напиши /reports чтобы начать.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()
