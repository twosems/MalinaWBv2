from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from storage.users import get_user_price_type, set_user_price_type
from bot.keyboards.keyboards import sales_report_settings_keyboard, sales_price_type_keyboard
from storage.users import get_user_article_mode, set_user_article_mode
from bot.keyboards.keyboards import articles_mode_keyboard, article_mode_human
from aiogram.exceptions import TelegramBadRequest
from storage.users import get_user_warehouse_filter, set_user_warehouse_filter
from bot.keyboards.keyboards import warehouse_filter_keyboard
router = Router()

# Главное меню настроек
@router.callback_query(F.data == "sales_report_settings")
async def sales_report_settings_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    price_type = await get_user_price_type(user_id)
    article_mode = await get_user_article_mode(user_id)
    warehouse_filter = await get_user_warehouse_filter(user_id)
    text = (
        "⚙️ <b>Настройки отчётов</b>\n"
        "\n"
        "💰 <b>Вид цен -</b> управляйте, какие цены будут выводиться в отчётах.\n"
        "🛒 <b>Артикулы продавца:</b> все, или только с остатком на складах.\n"
        "🏬 <b>Склады:-</b> все склады, или исключить СЦ.\n"
        "\n"
        "Нажмите на интересующую настройку ниже 👇"
    )

    await callback.message.edit_text(
        text,
        reply_markup=sales_report_settings_keyboard(price_type, article_mode, warehouse_filter),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "sales_price_type")
@router.callback_query(F.data.startswith("set_price_type:"))
async def open_sales_price_type(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if callback.data.startswith("set_price_type:"):
        price_type = callback.data.split(":", 1)[1]
        await set_user_price_type(user_id, price_type)
    else:
        price_type = await get_user_price_type(user_id)
    try:
        await callback.message.edit_text(
            "<b>Выберите тип цены для отчёта:</b>",
            reply_markup=sales_price_type_keyboard(price_type),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Уже выбран этот тип цены.", show_alert=False)
        else:
            raise

@router.callback_query(F.data == "articles_mode")
@router.callback_query(F.data.startswith("set_article_mode:"))
async def open_articles_mode(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if callback.data.startswith("set_article_mode:"):
        mode = callback.data.split(":", 1)[1]
        await set_user_article_mode(user_id, mode)
    else:
        mode = await get_user_article_mode(user_id)
    try:
        await callback.message.edit_text(
            "<b>Выберите режим вывода артикулов для отчётов:</b>",
            reply_markup=articles_mode_keyboard(mode),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Уже выбран этот вариант.", show_alert=False)
        else:
            raise

@router.callback_query(F.data == "warehouses_filter_mode")
@router.callback_query(F.data.startswith("set_warehouse_filter:"))
async def open_warehouse_filter_mode(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if callback.data.startswith("set_warehouse_filter:"):
        value = callback.data.split(":", 1)[1]
        await set_user_warehouse_filter(user_id, value)
    else:
        value = await get_user_warehouse_filter(user_id)
    try:
        await callback.message.edit_text(
            "<b>Фильтр складов:</b>\n\n"
            "Выберите вариант, который будет применяться по умолчанию во всех отчётах:",
            reply_markup=warehouse_filter_keyboard(value),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Уже выбран этот вариант.", show_alert=False)
        else:
            raise

