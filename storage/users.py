"""
storage/users.py

Описание:
- Асинхронная работа с доступом пользователей в PostgreSQL через SQLAlchemy.
- Операции: добавление, получение, обновление, удаление, работа с seller_name и trade_mark.

Требует: поля seller_name, trade_mark в модели UserAccess!
"""

from sqlalchemy.future import select
from sqlalchemy import update
from .db import AsyncSessionLocal
from .models import UserAccess
from datetime import datetime, timedelta

# Получить объект доступа пользователя по user_id (или None, если не найден)
async def get_user_access(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.user_id == user_id)
        )
        return result.scalar_one_or_none()

# Создать новую запись доступа для пользователя (если пользователь новый)
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

# Активировать или продлить пробный доступ пользователю до указанной даты
async def set_trial_access(user_id: int, until):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(trial_activated=True, trial_until=until)
        )
        await session.commit()

# Сохранить или обновить API-ключ Wildberries для пользователя
async def set_user_api_key(user_id: int, api_key: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(api_key=api_key)
        )
        await session.commit()

# Получить сохранённый API-ключ Wildberries для пользователя (или None, если не задан)
async def get_user_api_key(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess.api_key).where(UserAccess.user_id == user_id)
        )
        row = result.first()
        return row[0] if row else None

# Продлить платный доступ пользователя на указанное количество дней
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

# ------------------- Работа с seller_name и trade_mark -------------------

async def get_user_profile_info(user_id: int):
    """
    Получить seller_name и trade_mark для пользователя.
    :param user_id: int
    :return: объект с seller_name и trade_mark или None
    """
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
    """
    Сохранить seller_name и trade_mark для пользователя.
    """
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(seller_name=seller_name, trade_mark=trade_mark)
        )
        await session.commit()

# ------------------- Удаление API-ключа, seller info и аккаунта -------------------

async def remove_user_api_key(user_id: int):
    """
    Удалить API-ключ и seller info у пользователя.
    """
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(api_key=None, seller_name=None, trade_mark=None)
        )
        await session.commit()

async def remove_user_account(user_id: int):
    """
    Удалить пользователя (учётку) полностью.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            await session.delete(user)
            await session.commit()
