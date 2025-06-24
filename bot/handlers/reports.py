"""Report related handlers."""

from aiogram import Router, F
from aiogram.types import Message
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

__all__ = ["router", "reports_keyboard"]
