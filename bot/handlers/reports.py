"""Report related handlers."""

from bot.keyboards.inline import reports_keyboard
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from bot.keyboards.inline import reports_keyboard
router = Router()

@router.message(F.command("reports"))
async def reports_menu(message: Message) -> None:
    """Show main menu for reports section."""
    await message.answer(
        "📊 <b>Раздел отчётов</b>\n\nВыберите тип отчёта:",
        reply_markup=reports_keyboard(),
        parse_mode="HTML",
    )
@router.callback_query(F.data == "main_reports")
async def reports_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 <b>Раздел «Отчёты»</b>\n\n"
        "Здесь вы можете получить быстрый доступ к ключевым отчётам:\n\n"
        "📦 Остатки — узнать актуальные остатки товаров на складах.\n"
        "📈 Продажи — посмотреть динамику и статистику продаж.\n"
        "🏬 Хранение — контроль хранения и издержек на складах.\n"
        "🎯 Реклама — анализ расходов и эффективности рекламных кампаний.\n\n"
        "Выберите нужный отчёт или вернитесь в главное меню 👇",
        reply_markup=reports_keyboard(),
        parse_mode="HTML"
    )

# Реализуешь обработчики кнопок: report_stock, report_sales и т.д.

__all__ = ["router", "reports_keyboard"]