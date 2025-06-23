"""
bot/handlers/admin.py

Интуитивная админка:
- Список пользователей кнопками
- Для каждого пользователя действия: добавить дней, заблокировать, разблокировать, удалить, инфо
- Все действия на inline-кнопках, доступ только для админов (ADMINS)
"""

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMINS
from storage.db import AsyncSessionLocal
from storage.models import UserAccess
from storage.users import add_paid_days, get_user_access
from sqlalchemy.future import select
from sqlalchemy import update, delete

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

# --- Главное админ-меню (список пользователей) ---
@router.message((F.text == "🛠️ Админка") | (F.text == "/admin"))
async def admin_menu(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return

    # Получаем список user_id (можно сделать постранично, сейчас выводим до 20)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserAccess.user_id))
        users = [str(row[0]) for row in result.fetchall()][:20]

    if not users:
        await message.answer("В базе нет пользователей.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"👤 {uid}", callback_data=f"admin_user_{uid}")]
            for uid in users
        ]
    )
    await message.answer("Выбери пользователя:", reply_markup=keyboard)

# --- Кнопки действий с пользователем ---
@router.callback_query(F.data.startswith("admin_user_"))
async def admin_user_actions(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    user_id = int(callback.data.replace("admin_user_", ""))
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить дней", callback_data=f"admin_adddays_{user_id}")],
            [InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"admin_ban_{user_id}")],
            [InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"admin_unban_{user_id}")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_del_{user_id}")],
            [InlineKeyboardButton(text="ℹ️ Инфо", callback_data=f"admin_info_{user_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ]
    )
    await callback.message.edit_text(
        f"Действия для пользователя <b>{user_id}</b>:",
        parse_mode="HTML",
        reply_markup=keyboard
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
        await callback.message.edit_text("Пользователь не найден.")
        await callback.answer()
        return
    text = (
        f"<b>Пользователь {user_id}</b>\n"
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

# --- Добавить дней: спрашиваем сколько дней (отдельное состояние) ---
class AddDaysStates(StatesGroup):
    waiting_days = State()
    target_user_id = State()

@router.callback_query(F.data.startswith("admin_adddays_"))
async def ask_add_days(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    user_id = int(callback.data.replace("admin_adddays_", ""))
    await state.update_data(target_user_id=user_id)
    await state.set_state(AddDaysStates.waiting_days)
    await callback.message.edit_text(
        f"Сколько дней добавить пользователю <b>{user_id}</b>? (1-30)",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_user_{user_id}")]
        ])
    )
    await callback.answer()

@router.message(AddDaysStates.waiting_days)
async def process_add_days(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("target_user_id")
    try:
        days = int(message.text)
        if days < 1 or days > 30:
            await message.answer("Можно добавить от 1 до 30 дней. Введите снова:")
            return
        success = await add_paid_days(user_id, days)
        if success:
            await message.answer(
                f"✅ Пользователю {user_id} добавлено {days} дней платного доступа.",
            )
        else:
            await message.answer("❌ Пользователь не найден.")
        await state.clear()
    except Exception:
        await message.answer("Введите число дней (от 1 до 30):")

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
            [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="admin_back")]
        ])
    )
    await callback.answer()

# --- Назад к списку пользователей ---
@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return
    await admin_menu(callback.message)
    await callback.answer()
