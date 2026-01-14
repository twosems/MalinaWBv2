import aiohttp
import asyncio
from datetime import timedelta, datetime
import httpx
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_report_eta(callback, date_from, date_to):
    if date_from == date_to:
        period_text = f"<b>{date_from.strftime('%d.%m.%Y')}</b>"
    else:
        period_text = f"<b>{date_from.strftime('%d.%m.%Y')} — {date_to.strftime('%d.%m.%Y')}</b>"
    await callback.message.answer(
        f"⏳ Формируем отчёт за период {period_text}.\n"
        f"Пожалуйста, дождитесь завершения выгрузки!",
        parse_mode="HTML"
    )

async def get_sales_report_with_eta(api_key, date_from, date_to, max_retries=3):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
    headers = {"Authorization": str(api_key)}
    params = {
        "dateFrom": date_from.strftime("%Y-%m-%d"),
        "flag": 1 if date_from == date_to else 0
    }
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=30) as resp:
                    logger.info(f"API request attempt {attempt + 1}/{max_retries}, status: {resp.status}")
                    if resp.status == 200:
                        sales = await resp.json()
                        if date_from != date_to:
                            return [
                                item for item in sales
                                if date_from <= datetime.fromisoformat(item["date"][:10]) <= date_to
                            ]
                        return sales
                    elif resp.status == 401:
                        logger.error("Unauthorized: Invalid API key")
                        return {"error": "unauthorized"}
                    elif resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        return {"error": "rate_limit_exceeded"}
                    elif resp.status == 500:
                        logger.error("Server error on Wildberries side")
                        return {"error": "server_error"}
                    else:
                        logger.error(f"Unexpected API error: {resp.status} - {await resp.text()}")
                        return {"error": "unknown", "status": resp.status}
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return {"error": "network"}
    return {"error": "max_retries_exceeded"}

async def get_sales_report_for_period(api_key, date_from, date_to, max_retries=3):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
    headers = {"Authorization": str(api_key)}
    params = {
        "dateFrom": date_from.strftime("%Y-%m-%d"),
        "flag": 0
    }
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=30) as resp:
                    logger.info(f"API request attempt {attempt + 1}/{max_retries}, status: {resp.status}")
                    if resp.status == 200:
                        sales = await resp.json()
                        return [
                            item for item in sales
                            if date_from <= datetime.fromisoformat(item["date"][:10]) <= date_to
                        ]
                    elif resp.status == 401:
                        logger.error("Unauthorized: Invalid API key")
                        return []
                    elif resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        return []
                    elif resp.status == 500:
                        logger.error("Server error on Wildberries side")
                        return []
                    else:
                        logger.error(f"Unexpected API error: {resp.status} - {await resp.text()}")
                        return []
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return []
    return []

async def get_sales_report_for_day(api_key, date, max_retries=3):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/sales"
    headers = {"Authorization": str(api_key)}
    params = {
        "dateFrom": date.strftime("%Y-%m-%d"),
        "flag": 1
    }
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=30) as resp:
                    logger.info(f"API request attempt {attempt + 1}/{max_retries}, status: {resp.status}")
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 401:
                        logger.error("Unauthorized: Invalid API key")
                        return []
                    elif resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        return []
                    elif resp.status == 500:
                        logger.error("Server error on Wildberries side")
                        return []
                    else:
                        logger.error(f"Unexpected API error: {resp.status} - {await resp.text()}")
                        return []
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return []
    return []

async def get_stocks(api_key, date_from="2019-06-20", max_retries=3):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/stocks"
    headers = {"Authorization": f"Bearer {api_key}"}  # Добавляем префикс Bearer
    params = {"dateFrom": date_from}
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(trust_env=False, timeout=30.0) as client:
                resp = await client.get(url, headers=headers, params=params)
                logger.info(f"API request attempt {attempt + 1}/{max_retries}, status: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    logger.debug(f"Raw response sample: {data[:5]}...")  # Первые 5 элементов
                    return data
                elif resp.status_code == 401:
                    logger.error(f"Unauthorized: {resp.json().get('detail', 'No detail')}")
                    return {"error": "unauthorized", "detail": resp.json().get("detail", "empty Authorization header")}
                elif resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    return {"error": "rate_limit_exceeded"}
                elif resp.status_code == 500:
                    logger.error("Server error on Wildberries side")
                    return {"error": "server_error"}
                else:
                    logger.error(f"Unexpected API error: {resp.status_code} - {resp.text}")
                    return {"error": "unknown", "status": resp.status_code}
        except httpx.RequestError as e:
            logger.error(f"Network error: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return {"error": "network"}
    return {"error": "max_retries_exceeded"}
async def fetch_warehouses_from_api(api_key: str, max_retries=3):
    url = "https://supplies-api.wildberries.ru/api/v1/warehouses"
    headers = {"Authorization": api_key}
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as resp:
                    logger.info(f"API request attempt {attempt + 1}/{max_retries}, status: {resp.status}")
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 401:
                        logger.error("Unauthorized: Invalid API key")
                        return []
                    elif resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        return []
                    elif resp.status == 500:
                        logger.error("Server error on Wildberries side")
                        return []
                    else:
                        logger.error(f"Unexpected API error: {resp.status} - {await resp.text()}")
                        return []
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return []
    return []

# Восстановление оригинальной функции
async def get_all_articles_from_stocks(api_key, max_retries=3):
    stocks = await get_stocks(api_key, max_retries=max_retries)
    if isinstance(stocks, dict) and "error" in stocks:
        logger.error(f"Failed to get stocks: {stocks['error']}")
        return []
    if not stocks or not isinstance(stocks, list):
        logger.warning(f"Invalid or empty stocks data received: {stocks[:100] if isinstance(stocks, list) else stocks}")
        return []
    logger.debug(f"Processing stocks data: {len(stocks)} items")
    art_map = {}
    for item in stocks:
        art = item.get("supplierArticle")
        qty = item.get("quantity", 0)
        # Дополнительная проверка структуры данных
        if not isinstance(qty, (int, float)):
            logger.warning(f"Invalid quantity for article {art}: {qty}")
            continue
        if art and isinstance(art, str):
            in_stock = qty > 0 or art_map.get(art, False)
            art_map[art] = in_stock
            logger.debug(f"Processed article: {art}, qty: {qty}, in_stock: {in_stock}")
    if not art_map:
        logger.warning("No valid articles found in stocks data")
        return []
    result = [{"article": art, "in_stock": in_stock} for art, in_stock in art_map.items()]
    logger.info(f"Successfully processed {len(result)} unique articles")
    return result