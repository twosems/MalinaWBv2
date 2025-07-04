import asyncio
from sqlalchemy import text
from storage.db import AsyncSessionLocal
from storage.models import WarehouseCacheInfo
from datetime import datetime

async def test_cache_info_write(user_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM warehouse_cache_info"))
        info = WarehouseCacheInfo(updated_at=datetime.utcnow(), updated_by=user_id)
        session.add(info)
        await session.commit()
        print("Test cache info saved!")

asyncio.run(test_cache_info_write(123456789))
