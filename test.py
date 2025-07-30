# test_articles.py (отдельный файл для локального теста)
import asyncio
import httpx
API_KEY = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwNTIwdjEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc2OTIzNjEyMSwiaWQiOiIwMTk4NDJkOC0zMTA1LTc3MTMtODZlMS0zNjA1NTBjZjZmMDYiLCJpaWQiOjY1MjgzMzMsIm9pZCI6Mjc0MzIzLCJzIjoxMDg0LCJzaWQiOiI5YzY2MjgyMy05MzYwLTRhODUtODY2ZS0zZTZjMzQ4ZTk4OGIiLCJ0IjpmYWxzZSwidWlkIjo2NTI4MzMzfQ.p8G0K4nGnQoWNF1xof9d5n4ad0k0otVtVfXzT4ivUAPPsxEtyOSjk2jAc9I8ByDqCuSxInCbfco8YyRGjGFoQw"

async def get_all_articles(api_key: str) -> list[str]:
    url = "https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"limit": 1000, "offset": 0}

    async with httpx.AsyncClient(trust_env=False, timeout=30.0) as client:
        resp = await client.get(url, headers=headers, params=params)
        print(f"Статус ответа: {resp.status_code}")  # <--- статус запроса
        resp.raise_for_status()
        data = resp.json()
        page = data.get("data", [])
        print(f"Найдено товаров: {len(page)}")       # <--- сколько позиций нашлось
        for item in page:
            art = item.get("vendorCode")
            if art:
                print(art)
        return [item["vendorCode"] for item in page if "vendorCode" in item]

async def main():
    await get_all_articles(API_KEY)

if __name__ == "__main__":
    asyncio.run(main())
