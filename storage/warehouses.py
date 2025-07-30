"""
storage/warehouses.py

Асинхронные функции для ГЛОБАЛЬНОГО кэширования списка складов Wildberries в PostgreSQL.
- Список складов общий для всех пользователей!
- Кэш обновляется не чаще, чем раз в 12 часов (по API любого пользователя).
- Любой пользователь может инициировать обновление при входе, если кэш устарел.
- Хранится информация о времени и пользователе, который обновил кэш.
"""

from sqlalchemy.future import select
from sqlalchemy import delete, func
from datetime import datetime, timedelta
from .db import AsyncSessionLocal
from .models import Warehouse, WarehouseCacheInfo
from sqlalchemy import text

async def get_last_warehouses_update():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.max(Warehouse.updated_at))
        )
        return result.scalar_one()

async def cache_warehouses(warehouses: list, updated_by: int = None):
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Warehouse))
        now = datetime.utcnow()
        for w in warehouses:
            wh = Warehouse(
                id=w.get("ID"),
                name=w.get("name"),
                address=w.get("address"),
                workTime=w.get("workTime"),
                acceptsQR=w.get("acceptsQR"),
                isActive=w.get("isActive"),
                updated_at=now
            )
            session.add(wh)
        await session.commit()
    if updated_by is not None:
        await set_cache_update_info(updated_by)

async def get_cached_warehouses():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Warehouse))
        return result.scalars().all()

async def get_cached_warehouses_dicts():
    warehouses = await get_cached_warehouses()
    return [
        {
            "id": wh.id,
            "name": wh.name,
            "address": wh.address,
            "workTime": wh.workTime,
            "acceptsQR": wh.acceptsQR,
            "isActive": wh.isActive,
            "updated_at": wh.updated_at
        }
        for wh in warehouses
    ]


async def need_update_warehouses_cache():
    last_update = await get_last_warehouses_update()
    now = datetime.utcnow()
    return (not last_update) or ((now - last_update) > timedelta(hours=12))

async def set_cache_update_info(user_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM warehouse_cache_info"))
        info = WarehouseCacheInfo(updated_at=datetime.utcnow(), updated_by=user_id)
        session.add(info)
        await session.commit()

async def get_cache_update_info():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(WarehouseCacheInfo).order_by(WarehouseCacheInfo.updated_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()
