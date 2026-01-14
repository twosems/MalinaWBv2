"""
storage/users.py

Функции для асинхронной работы с доступом пользователей через SQLAlchemy (PostgreSQL).
- Получение, создание, обновление пользователей и их баланса.
- Списание баланса только за реально оплаченные дни (баланс никогда не уходит в минус).
- Работа с пробным доступом, API-ключами, архивированием и профилями.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Optional, List

from sqlalchemy.future import select
from sqlalchemy import update

from .models import UserAccess, BillingHistory
from .db import AsyncSessionLocal

logger = logging.getLogger(__name__)

DAILY_COST = 399 // 30  # 13 рублей в день


# Получить объект доступа пользователя по user_id
async def get_user_access(user_id: int) -> Optional[UserAccess]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.user_id == user_id)
        )
        return result.scalar_one_or_none()


# Списание баланса при входе пользователя (баланс не уходит в минус)
async def update_balance_on_access(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return

        now = datetime.now(tz=timezone.utc)
        last_billing = user.last_billing or user.paid_until or user.trial_until or now
        days_passed = (now.date() - last_billing.date()).days

        if days_passed > 0:
            current_balance = user.balance or 0
            max_payable_days = min(days_passed, max(current_balance // DAILY_COST, 0))
            new_balance = current_balance - max_payable_days * DAILY_COST
            new_last_billing = (
                last_billing + timedelta(days=max_payable_days)
                if max_payable_days > 0 else last_billing
            )

            await session.execute(
                update(UserAccess)
                .where(UserAccess.user_id == user_id)
                .values(balance=new_balance, last_billing=new_last_billing)
            )
            await session.commit()
        elif not user.last_billing:
            await session.execute(
                update(UserAccess)
                .where(UserAccess.user_id == user_id)
                .values(last_billing=now)
            )
            await session.commit()


# <<< НОВОЕ >>> Ежедневная массовая актуализация баланса
async def daily_balance_update():
    """
    Проходит по всем пользователям и списывает дни согласно логике update_balance_on_access.
    Безопасна к нулевому/отрицательному балансу — в минус не уводит.
    """
    # Сначала берём список user_id одним запросом
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserAccess.user_id))
        user_ids: List[int] = list(result.scalars().all())

    # Затем последовательным циклом прогоняем пользователей
    # (если потребуется — можно шардировать/батчить/параллелить)
    for uid in user_ids:
        try:
            await update_balance_on_access(uid)
        except Exception as e:
            logger.exception("daily_balance_update: failed for user_id=%s: %s", uid, e)


# Пополнение баланса
async def add_balance(user_id: int, amount: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess.balance).where(UserAccess.user_id == user_id)
        )
        row = result.first()
        old_balance = row[0] if row else 0
        new_balance = (old_balance or 0) + amount
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(balance=new_balance)
        )
        await session.commit()


# Поиск пользователя по seller_name (для восстановления)
async def find_user_by_seller_name(seller_name: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.seller_name == seller_name)
        )
        return result.scalar_one_or_none()


# Перепривязка user_id к seller_name
async def update_user_id_by_seller_name(seller_name: str, new_user_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.seller_name == seller_name)
            .values(user_id=new_user_id)
        )
        await session.commit()


# Восстановление по балансу
async def can_restore_access(seller_name: str) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.seller_name == seller_name)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        return (user.balance or 0) > 0


# Создание нового пользователя
async def create_user_access(user_id: int):
    async with AsyncSessionLocal() as session:
        access = UserAccess(
            user_id=user_id,
            paid_until=None,
            trial_until=None,
            trial_activated=False,
            api_key=None,
            seller_name=None,
            trade_mark=None,
            balance=0,
            last_billing=datetime.now(tz=timezone.utc),
        )
        session.add(access)
        await session.commit()


# Пробный доступ
async def set_trial_access(user_id: int, until: datetime):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(
                trial_activated=True,
                trial_until=until,
                paid_until=until,
            )
        )
        await session.commit()


# Работа с API-ключом
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


# Получение инфо по профилю пользователя
async def get_user_profile_info(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess.seller_name, UserAccess.trade_mark)
            .where(UserAccess.user_id == user_id)
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


# Архивирование/Удаление пользователя (user_id)
async def remove_user_api_key(user_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(api_key=None)
        )
        await session.commit()


async def remove_user_account(user_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(
                api_key=None,
                trial_activated=False,
                is_archived=True,
            )
        )
        await session.commit()


async def find_archived_user_by_seller_name(seller_name: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(
                UserAccess.seller_name == seller_name,
                UserAccess.is_archived == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()


# Проверка активного доступа пользователя
def has_active_access(user) -> bool:
    """
    True, если у пользователя:
    - положительный баланс, или
    - активный пробный период (trial_activated и trial_until не истёк),
    - и не архивирован.
    """
    if not user:
        return False

    now = datetime.now(tz=timezone.utc)
    if getattr(user, "is_archived", False):
        return False

    balance = getattr(user, "balance", 0)
    if balance is not None and balance > 0:
        return True

    trial_activated = getattr(user, "trial_activated", False)
    trial_until = getattr(user, "trial_until", None)
    if trial_activated and trial_until and now <= trial_until:
        return True

    return False


from config import ADMINS  # импорт оставил как у вас


async def get_admin_token():
    """Возвращает api_key первого админа из списка ADMINS"""
    admin_id = ADMINS[0]
    admin_access = await get_user_access(admin_id)
    if admin_access and getattr(admin_access, "api_key", None):
        return admin_access.api_key
    return None


async def get_user_price_type(user_id: int) -> str:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess.price_type).where(UserAccess.user_id == user_id)
        )
        row = result.first()
        return row[0] if row and row[0] else "priceWithDisc"


async def set_user_price_type(user_id: int, price_type: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(price_type=price_type)
        )
        await session.commit()


async def get_user_article_mode(user_id: int) -> str:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess.article_mode).where(UserAccess.user_id == user_id)
        )
        row = result.first()
        return row[0] if row and row[0] else "all"


async def set_user_article_mode(user_id: int, article_mode: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(article_mode=article_mode)
        )
        await session.commit()


async def get_user_warehouse_filter(user_id: int) -> str:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess.warehouse_filter).where(UserAccess.user_id == user_id)
        )
        row = result.first()
        return row[0] if row and row[0] else "all"


async def set_user_warehouse_filter(user_id: int, value: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(UserAccess)
            .where(UserAccess.user_id == user_id)
            .values(warehouse_filter=value)
        )
        await session.commit()
