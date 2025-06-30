import asyncio
from sqlalchemy.future import select  # <-- ВАЖНО!
from storage.db import AsyncSessionLocal
from storage.models import UserAccess

async def print_user_status(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserAccess).where(UserAccess.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            print(f"user_id: {user.user_id}")
            print(f"seller_name: {user.seller_name!r}")
            print(f"is_archived: {getattr(user, 'is_archived', None)}")
            print(f"paid_until: {user.paid_until}")
            print(f"trial_until: {user.trial_until}")
            print(f"api_key: {user.api_key!r}")
        else:
            print(f"Пользователь с user_id={user_id} не найден.")

if __name__ == "__main__":
    # Подставь свой user_id!
    asyncio.run(print_user_status(699875303))
