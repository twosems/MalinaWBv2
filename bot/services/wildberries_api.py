import aiohttp
import asyncio
from datetime import timedelta, datetime
import httpx

async def send_report_eta(callback, date_from, date_to):
    # Показать пользователю период или день, без оценки ETA в минутах
    if date_from == date_to:
        period_text = f"<b>{date_from.strftime('%d.%m.%Y')}</b>"
    else:
        period_text = f"<b>{date_from.strftime('%d.%m.%Y')} — {date_to.strftime('%d.%m.%Y')}</b>"
    await callback.message.answer(
        f"⏳ Формируем отчёт за период {period_text}.\n"
        f"Пожалуйста, дождитесь завершения выгрузки!",
        parse_mode="HTML"
    )
async def get_sales_report_with_eta(api_key, date_from, date_to):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
    headers = {"Authorization": str(api_key)}
    params = {
        "dateFrom": date_from.strftime("%Y-%m-%d"),
        "flag": 1 if date_from == date_to else 0
    }
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 429:
                    retry = int(resp.headers.get("X-Ratelimit-Retry", "60"))
                    print(f"ЛИМИТ! Ожидание {retry} сек.")
                    return {"error": "ratelimit", "retry": retry}
                if resp.status == 200:
                    sales = await resp.json()
                    if date_from != date_to:
                        return [
                            item for item in sales
                            if date_from <= datetime.fromisoformat(item["date"][:10]) <= date_to
                        ]
                    else:
                        return sales
                else:
                    return {"error": "other"}

async def get_sales_report(api_key: str, date_from: str, date_to: str):
    url = "https://suppliers-stats.wildberries.ru/api/v1/supplier/sales"
    params = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "key": api_key
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            return await resp.json()

async def get_sales_report_for_day(api_key, date):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
    headers = {"Authorization": str(api_key)}
    params = {
        "dateFrom": date.strftime("%Y-%m-%d"),
        "flag": 1
    }
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 429:
                    retry = int(resp.headers.get("X-Ratelimit-Retry", "60"))
                    await asyncio.sleep(retry)
                else:
                    return []

async def get_sales_report_for_period(api_key, date_from, date_to):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
    headers = {"Authorization": str(api_key)}
    params = {
        "dateFrom": date_from.strftime("%Y-%m-%d"),
        "flag": 0
    }
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    sales = await resp.json()
                    result = [
                        item for item in sales
                        if date_from <= datetime.fromisoformat(item["date"][:10]) <= date_to
                    ]
                    return result
                elif resp.status == 429:
                    retry = int(resp.headers.get("X-Ratelimit-Retry", "60"))
                    await asyncio.sleep(retry)
                else:
                    return []

async def fetch_warehouses_from_api(api_key: str):
    url = "https://supplies-api.wildberries.ru/api/v1/warehouses"
    headers = {"Authorization": api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            return []


async def get_stocks(api_key, date_from="2019-06-20"):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/stocks"
    headers = {"Authorization": str(api_key)}
    params = {"dateFrom": date_from}
    async with httpx.AsyncClient(trust_env=False, timeout=30.0) as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

async def get_all_articles_from_stocks(api_key):
    stocks = await get_stocks(api_key)
    art_map = {}
    for item in stocks:
        art = item.get("supplierArticle")
        qty = item.get("quantity", 0)
        if art:
            # Если артикул уже есть и хоть в одной позиции qty>0 — отмечаем как in_stock
            in_stock = qty > 0 or art_map.get(art, False)
            art_map[art] = in_stock
    # Преобразуем в список dict-ов
    return [{"article": art, "in_stock": in_stock} for art, in_stock in art_map.items()]
