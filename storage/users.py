"""
users.py — асинхронные функции для работы с доступами пользователей в базе данных PostgreSQL через SQLAlchemy.

Структура и принцип работы:
- Все функции используют асинхронную сессию SQLAlchemy (AsyncSessionLocal) и модель UserAccess.
- Доступ пользователя хранит:
    - user_id: ID пользователя Telegram (PRIMARY KEY)
    - paid_until: дата и время окончания платного доступа
    - trial_until: дата и время окончания пробного периода
    - trial_activated: активирован ли пробный доступ
    - api_key: API-ключ Wildberries пользователя (может быть пустым)

Реализованные функции:
- get_user_access(user_id): получить объект доступа пользователя.
- create_user_access(user_id): создать новую запись доступа (если пользователь новый).
- set_trial_access(user_id, until): активировать/продлить пробный доступ пользователю.
- set_user_api_key(user_id, api_key): сохранить или обновить API-ключ пользователя.
- get_user_api_key(user_id): получить сохранённый API-ключ пользователя.

Все операции выполняются атомарно и асинхронно, что обеспечивает корректную работу с большим количеством пользователей.
"""

from sqlalchemy.future import select
from sqlalchemy import update
from .db import AsyncSessionLocal
from .models import UserAccess

# Получить доступ пользователя по user_id (возвращает объект UserAccess или None)
async def get_user_access(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.user_id == user_id)
        )
        return result.scalar_one_or_none()

# Создать новую запись для пользователя (использовать для новых user_id)
async def create_user_access(user_id: int):
    async with AsyncSessionLocal() as session:
        access = UserAccess(
            user_id=user_id,
            paid_until=None,
            trial_until=None,
            trial_activated=False,
            api_key=None
        )
        session.add(access)
        await session.commit()

# Активировать или продлить пробный доступ до определённой даты
async def set_trial_access(user_id: int, until):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(trial_activated=True, trial_until=until)
        )
        await session.commit()

# Сохранить или обновить API-ключ пользователя (Wildberries API)
async def set_user_api_key(user_id: int, api_key: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(api_key=api_key)
        )
        await session.commit()

# Получить сохранённый API-ключ пользователя (или None, если не задан)
async def get_user_api_key(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess.api_key).where(UserAccess.user_id == user_id)
        )
        row = result.first()
        return row[0] if row else None
