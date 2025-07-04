import aiohttp

# Пример функции для получения отчёта по продажам (дополни своими параметрами)
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

# Функция для получения списка складов по API-ключу
async def fetch_warehouses_from_api(api_key: str):
    url = "https://supplies-api.wildberries.ru/api/v1/warehouses"
    headers = {"Authorization": api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            return []

import httpx

async def get_stocks(api_key, date_from="2019-06-20"):
    url = "https://statistics-api.wildberries.ru/api/v1/supplier/stocks"
    headers = {"Authorization": str(api_key)}
    params = {"dateFrom": date_from}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()
