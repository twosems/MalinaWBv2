"""
storage/users.py

Описание:
- Асинхронная работа с доступом пользователей в PostgreSQL через SQLAlchemy.
- Операции: добавление, получение, обновление, удаление, восстановление, архивирование по seller_name.
"""

from sqlalchemy.future import select
from sqlalchemy import update
from .db import AsyncSessionLocal
from .models import UserAccess
from datetime import datetime, timedelta

# Получить объект доступа пользователя по user_id
async def get_user_access(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.user_id == user_id)
        )
        return result.scalar_one_or_none()

# Поиск пользователя по seller_name (для восстановления)
async def find_user_by_seller_name(seller_name: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.seller_name == seller_name)
        )
        return result.scalar_one_or_none()

# Перепривязать Telegram user_id к seller_name
async def update_user_id_by_seller_name(seller_name: str, new_user_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.seller_name == seller_name)
            .values(user_id=new_user_id)
        )
        await session.commit()

# Есть ли у магазина (seller_name) положительный баланс для восстановления
async def can_restore_access(seller_name: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.seller_name == seller_name)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        now = datetime.utcnow()
        return (user.paid_until and user.paid_until > now) or (user.trial_until and user.trial_until > now)

# Создать нового пользователя (user_id)
async def create_user_access(user_id: int):
    async with AsyncSessionLocal() as session:
        access = UserAccess(
            user_id=user_id,
            paid_until=None,
            trial_until=None,
            trial_activated=False,
            api_key=None,
            seller_name=None,
            trade_mark=None
        )
        session.add(access)
        await session.commit()

# --- Пробный доступ ---
async def set_trial_access(user_id: int, until):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(
                trial_activated=True,
                trial_until=until,
                paid_until=until
            )
        )
        await session.commit()

# --- Работа с API-ключом ---
async def set_user_api_key(user_id: int, api_key: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(api_key=api_key)
        )
        await session.commit()

async def get_user_api_key(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess.api_key).where(UserAccess.user_id == user_id)
        )
        row = result.first()
        return row[0] if row else None

# --- Платная подписка ---
async def add_paid_days(user_id: int, days: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.user_id == user_id)
        )
        user_access = result.scalar_one_or_none()
        if not user_access:
            return False

        now = datetime.utcnow()
        paid_until = user_access.paid_until or now
        if paid_until < now:
            paid_until = now

        new_paid_until = paid_until + timedelta(days=days)
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(paid_until=new_paid_until)
        )
        await session.commit()
        return True

# --- seller_name/trade_mark ---
async def get_user_profile_info(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess.seller_name, UserAccess.trade_mark).where(UserAccess.user_id == user_id)
        )
        row = result.first()
        if row:
            class Info:
                seller_name = row[0]
                trade_mark = row[1]
            return Info()
        return None

async def set_user_profile_info(user_id: int, seller_name: str, trade_mark: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(seller_name=seller_name, trade_mark=trade_mark)
        )
        await session.commit()

# --- Удаление/Архивирование ---
async def remove_user_api_key(user_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(api_key=None, seller_name=None, trade_mark=None)
        )
        await session.commit()

# ВАЖНО: НЕ УДАЛЯЕМ, А АРХИВИРУЕМ user_id (для восстановления)
async def remove_user_account(user_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(user_id=None, api_key=None)
        )
        await session.commit()
