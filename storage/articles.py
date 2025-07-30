from sqlalchemy.future import select
from sqlalchemy import delete
from datetime import datetime
from .db import AsyncSessionLocal
from .models import Article

async def cache_articles(user_id: int, articles: list[dict]):
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Article).where(Article.user_id == user_id))
        now = datetime.utcnow()
        for a in articles:
            session.add(Article(
                user_id=user_id,
                supplier_article=a["article"],
                in_stock=a["in_stock"],
                updated_at=now
            ))
        await session.commit()


async def get_cached_articles(user_id: int) -> list[str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Article.supplier_article).where(Article.user_id == user_id)
        )
        return [row[0] for row in result.fetchall()]

# Все артикулы
async def get_all_articles(user_id: int) -> list[str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Article.supplier_article).where(Article.user_id == user_id)
        )
        return [row[0] for row in result.fetchall()]

# Только с остатком
async def get_in_stock_articles(user_id: int) -> list[str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Article.supplier_article).where(Article.user_id == user_id, Article.in_stock == True)
        )
        return [row[0] for row in result.fetchall()]

# Только без остатка
async def get_out_of_stock_articles(user_id: int) -> list[str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Article.supplier_article).where(Article.user_id == user_id, Article.in_stock == False)
        )
        return [row[0] for row in result.fetchall()]
