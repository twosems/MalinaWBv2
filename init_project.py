# test_wb_api.py

import asyncio
import aiohttp

async def test_wb_api():
    print("=== Проверка API-ключа Wildberries ===")
    api_key = input("Вставьте ваш API-ключ Wildberries:\n").strip()
    url = 'https://common-api.wildberries.ru/api/v1/seller-info'
    headers = {'Authorization': api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            print(f"\nHTTP STATUS: {resp.status}")
            try:
                data = await resp.json()
                print("Ответ WB (JSON):")
                for k, v in data.items():
                    print(f"  {k}: {v}")
            except Exception as e:
                text = await resp.text()
                print("Не удалось декодировать JSON.")
                print("Сырой ответ WB:")
                print(text)

if __name__ == "__main__":
    asyncio.run(test_wb_api())
