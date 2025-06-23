# bot/services/wildberries_api.py

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
