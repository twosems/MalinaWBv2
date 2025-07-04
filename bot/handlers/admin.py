"""
bot/handlers/admin.py

Интуитивная админка:
- Разделы: Пользователи и Общее
- Пользователи: список пользователей кнопками, действия (баланс, блок, аннулировать триал, удалить, инфо)
- Общее: принудительное обновление складов, просмотр информации кеша складов
- Все действия на inline-кнопках, доступ только для админов (ADMINS)
"""

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMINS
from storage.db import AsyncSessionLocal
from storage.models import UserAccess
from storage.users import add_balance, get_user_access, get_admin_token
from storage.warehouses import cache_warehouses, get_cache_update_info
from bot.handlers.api_entry import get_warehouses  # твоя функция для запроса WB API
from sqlalchemy import select, update, delete
import logging
from bot.services.wildberries_api import fetch_warehouses_from_api
router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_common")]]
    )

# --- Главное админ-меню ---
@router.message((F.text == "🛠️ Админка") | (F.text == "/admin"))
async def admin_menu(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton(text="⚙️ Общее", callback_data="admin_common")]
        ]
    )
    await message.answer("Админка. Выберите раздел:", reply_markup=keyboard)

# --- Меню пользователей ---
@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserAccess.user_id))
        users = [str(row[0]) for row in result.fetchall()][:20]

    if not users:
        await callback.message.edit_text("В базе нет пользователей.", reply_markup=back_keyboard())
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=f"👤 {uid}", callback_data=f"admin_user_{uid}")] for uid in users
                        ] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]]
    )
    await callback.message.edit_text("Выбери пользователя:", reply_markup=keyboard)
    await callback.answer()

# --- Кнопки действий с пользователем ---
@router.callback_query(F.data.startswith("admin_user_"))
async def admin_user_actions(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    user_id = int(callback.data.replace("admin_user_", ""))
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Изменить баланс", callback_data=f"admin_addmoney_{user_id}")],
            [InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"admin_ban_{user_id}")],
            [InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"admin_unban_{user_id}")],
            [InlineKeyboardButton(text="❌ Аннулировать триал", callback_data=f"admin_canceltrial_{user_id}")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_del_{user_id}")],
            [InlineKeyboardButton(text="ℹ️ Инфо", callback_data=f"admin_info_{user_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_users")]
        ]
    )
    await callback.message.edit_text(
        f"Действия для пользователя <b>{user_id}</b>:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

# --- Аннулировать пробный доступ ---
@router.callback_query(F.data.startswith("admin_canceltrial_"))
async def admin_cancel_trial(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    user_id = int(callback.data.replace("admin_canceltrial_", ""))
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(trial_activated=False, trial_until=None, paid_until=None)
        )
        await session.commit()
    await callback.message.edit_text(
        f"❌ Пробный доступ пользователя <b>{user_id}</b> аннулирован.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_user_{user_id}")]
        ])
    )
    await callback.answer()

# --- Информация о пользователе ---
@router.callback_query(F.data.startswith("admin_info_"))
async def admin_info(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    user_id = int(callback.data.replace("admin_info_", ""))
    access = await get_user_access(user_id)
    if not access:
        await callback.message.edit_text("Пользователь не найден.", reply_markup=back_keyboard())
        await callback.answer()
        return
    text = (
        f"<b>Пользователь {user_id}</b>\n"
        f"💰 Баланс: <code>{getattr(access, 'balance', 0)}₽</code>\n"
        f"Платный доступ до: <code>{access.paid_until}</code>\n"
        f"Пробный до: <code>{access.trial_until}</code>\n"
        f"Пробный активирован: <code>{access.trial_activated}</code>\n"
        f"API ключ: <code>{access.api_key if access.api_key else '-'}</code>"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_user_{user_id}")]
        ]
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()

# --- Изменение баланса: спрашиваем сумму (отдельное состояние) ---
class AddMoneyStates(StatesGroup):
    waiting_amount = State()
    target_user_id = State()

@router.callback_query(F.data.startswith("admin_addmoney_"))
async def ask_add_money(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    user_id = int(callback.data.replace("admin_addmoney_", ""))
    await state.update_data(target_user_id=user_id)
    await state.set_state(AddMoneyStates.waiting_amount)
    await callback.message.edit_text(
        f"На какую сумму изменить баланс пользователя <b>{user_id}</b>?\n\n"
        f"Введите положительное число для пополнения или отрицательное для списания (например, <code>+399</code> или <code>-13</code>):",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_user_{user_id}")]
        ])
    )
    await callback.answer()

@router.message(AddMoneyStates.waiting_amount)
async def process_add_money(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("target_user_id")
    try:
        amount = int(message.text.replace('+', '').replace(' ', ''))
        await add_balance(user_id, amount)
        access = await get_user_access(user_id)
        await message.answer(
            f"✅ Баланс пользователя <b>{user_id}</b> изменён на {amount:+}₽.\n"
            f"💰 Новый баланс: <b>{getattr(access, 'balance', 0)}₽</b>",
            parse_mode="HTML",
        )
        await state.clear()
    except Exception:
        await message.answer("Введите целое число (например, <code>+399</code> или <code>-13</code>):", parse_mode="HTML")

# --- Блокировка пользователя ---
@router.callback_query(F.data.startswith("admin_ban_"))
async def admin_ban(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    user_id = int(callback.data.replace("admin_ban_", ""))
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(trial_activated=True, paid_until=None, trial_until=None)
        )
        await session.commit()
    await callback.message.edit_text(
        f"🚫 Пользователь {user_id} заблокирован (доступ обнулён).",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_user_{user_id}")]
        ])
    )
    await callback.answer()

# --- Разблокировка пользователя ---
@router.callback_query(F.data.startswith("admin_unban_"))
async def admin_unban(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    user_id = int(callback.data.replace("admin_unban_", ""))
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(trial_activated=False, paid_until=None, trial_until=None)
        )
        await session.commit()
    await callback.message.edit_text(
        f"✅ Пользователь {user_id} разблокирован (может снова активировать пробный доступ).",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_user_{user_id}")]
        ])
    )
    await callback.answer()

# --- Удаление пользователя ---
@router.callback_query(F.data.startswith("admin_del_"))
async def admin_del(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    user_id = int(callback.data.replace("admin_del_", ""))
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(UserAccess).where(UserAccess.user_id == user_id)
        )
        await session.commit()
    await callback.message.edit_text(
        f"🗑 Пользователь {user_id} удалён из базы.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="admin_users")]
        ])
    )
    await callback.answer()

# --- Меню общих функций ---
@router.callback_query(F.data == "admin_common")
async def admin_common(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить склады", callback_data="admin_update_warehouses")],
            [InlineKeyboardButton(text="📋 Просмотреть информацию кеша складов", callback_data="admin_view_warehouses_cache")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ]
    )
    await callback.message.edit_text("Общие админ-функции:", reply_markup=keyboard)
    await callback.answer()

# --- Просмотр информации о кешировании складов ---
@router.callback_query(F.data == "admin_view_warehouses_cache")
async def admin_view_warehouses_cache(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    info = await get_cache_update_info()
    if info:
        updated_at_str = info.updated_at.strftime('%d.%m.%Y %H:%M:%S')
        updated_by_str = str(info.updated_by) if info.updated_by else "неизвестно"
        text = (
            f"<b>Последнее обновление кеша складов:</b> {updated_at_str}\n"
            f"<b>Обновил пользователь (user_id):</b> {updated_by_str}"
        )
    else:
        text = "Информация о кешировании складов отсутствует."

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_update_warehouses")
async def admin_update_warehouses(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    api_key = await get_admin_token()
    logging.info(f"Admin API key: {api_key}")
    if not api_key:
        await callback.message.edit_text(
            "❌ У администратора не найден валидный API-ключ для Wildberries.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return

    await callback.message.edit_text("⏳ Обновляем список складов с Wildberries...")

    try:
        warehouses = await fetch_warehouses_from_api(api_key)
        if warehouses:
            logging.info(f"[WAREHOUSES] Обновление кеша складов инициировано user_id={callback.from_user.id}")
            await cache_warehouses(warehouses, updated_by=callback.from_user.id)
            info = await get_cache_update_info()
            updated_at_str = info.updated_at.strftime('%d.%m.%Y %H:%M:%S') if info else "неизвестно"
            updated_by_str = str(info.updated_by) if info and info.updated_by else "неизвестно"
            await callback.message.edit_text(
                f"✅ Склады успешно обновлены!\n\n"
                f"Последнее обновление: {updated_at_str}\n"
                f"Обновил пользователь: {updated_by_str}",
                reply_markup=back_keyboard()
            )
        else:
            await callback.message.edit_text("❌ Не удалось получить список складов с Wildberries.", reply_markup=back_keyboard())
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка обновления складов: {e}", reply_markup=back_keyboard())
    await callback.answer()

# --- Назад в меню "Общее" ---
@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return
    await admin_menu(callback.message)
    await callback.answer()