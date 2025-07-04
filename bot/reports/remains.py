
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.keyboards.keyboards import reports_keyboard  # или твоя клавиатура пагинации
from storage.users import get_user_api_key
from bot.services.wildberries_api import get_stocks
from bot.utils.pagination import build_pagination_keyboard
from bot.utils.csv_export import export_to_csv
from aiogram.types import InputFile

import csv
import io

router = Router()
PER_PAGE = 10

@router.callback_query(F.data.regexp(r"^report_remains(_page_)?(\d+)?$"))
async def report_remains(callback: CallbackQuery):
    user_id = callback.from_user.id

    # 1. Отправляем сообщение о формировании отчёта с анимацией точек
    msg = await callback.message.edit_text("⏳ Формируем отчёт", parse_mode="HTML")
    dots_task = asyncio.create_task(animate_dots(msg))

    try:
        # 2. Получаем API-ключ пользователя
        api_key = await get_user_api_key(user_id)
        if not api_key:
            dots_task.cancel()
            await msg.edit_text(
                "❗ Для просмотра остатков необходимо ввести API-ключ.",
                parse_mode="HTML"
            )
            return

        # 3. Получаем остатки с WB
        try:
            items = await get_stocks(api_key)
        except Exception as e:
            dots_task.cancel()
            await msg.edit_text(
                f"❗ Не удалось получить остатки.\nОшибка: {e}",
                parse_mode="HTML"
            )
            return

        if not items:
            dots_task.cancel()
            await msg.edit_text(
                "❗ Остатков не найдено.",
                parse_mode="HTML"
            )
            return

        # 4. Группируем по складам
        warehouse_data = {}
        for item in items:
            qty = item.get("quantity", 0)
            if qty == 0:
                continue
            wh = item.get("warehouseName", "Неизвестно")
            art = item.get("supplierArticle", "Без артикула")
            name = item.get("subject", "Без предмета")
            if wh not in warehouse_data:
                warehouse_data[wh] = []
            warehouse_data[wh].append((art, name, qty))

        if not warehouse_data:
            dots_task.cancel()
            await msg.edit_text(
                "❗ Все склады пусты!",
                parse_mode="HTML"
            )
            return

        # 5. Пагинация
        import re
        m = re.match(r"^report_remains(?:_page_)?(\d+)?$", callback.data)
        page = int(m.group(1)) if m and m.group(1) else 1

        warehouses = list(warehouse_data.items())
        total = len(warehouses)
        pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE
        page_items = warehouses[start:end]

        # 6. Формируем текст
        text_blocks = []
        for wh, products in page_items:
            text = f"🏬 <b>Склад:</b> {wh}\n"
            for art, name, qty in sorted(products, key=lambda x: (-x[2], x[0])):
                text += f"  • <b>{art}</b> ({name}): <b>{qty}</b> шт\n"
            text_blocks.append(text)
        final_text = "\n\n".join(text_blocks)
        final_text += f"\n\n<b>Страница {page} из {pages}</b>"

        kb = build_pagination_keyboard(
            total=total,
            page=page,
            per_page=PER_PAGE,
            prefix="report_remains_page_",
            back_callback="main_reports",
            add_export=True  # <--- вот тут!


        )

        # 7. Останавливаем анимацию точек и выводим результат
        dots_task.cancel()
        await msg.edit_text(final_text, reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        dots_task.cancel()
        await msg.edit_text(f"❗ Неизвестная ошибка: {e}")

async def animate_dots(msg):
    dots = ["⏳ Формируем отчёт.", "⏳ Формируем отчёт..", "⏳ Формируем отчёт..."]
    i = 0
    while True:
        await asyncio.sleep(0.7)
        try:
            await msg.edit_text(dots[i % 3], parse_mode="HTML")
        except Exception:
            break
        i += 1
from aiogram.types.input_file import BufferedInputFile
import csv
import io

@router.callback_query(F.data == "report_remains_export_csv")
async def report_remains_export_csv(callback: CallbackQuery):
    user_id = callback.from_user.id

    progress_msg = await callback.message.answer("⏳ Формируем CSV-отчёт...", parse_mode="HTML")
    api_key = await get_user_api_key(user_id)
    if not api_key:
        await progress_msg.edit_text(
            "❗ Для экспорта необходим API-ключ.",
            parse_mode="HTML"
        )
        return

    try:
        items = await get_stocks(api_key)
    except Exception as e:
        await progress_msg.edit_text(
            f"❗ Не удалось получить остатки.\nОшибка: {e}",
            parse_mode="HTML"
        )
        return

    stocks = [item for item in items if item.get("quantity", 0) > 0]
    if not stocks:
        await progress_msg.edit_text(
            "❗ Остатков для экспорта не найдено.",
            parse_mode="HTML"
        )
        return

    # --- Группируем по складам для красивого Telegram-style CSV ---
    warehouse_data = {}
    for item in stocks:
        wh = item.get("warehouseName", "Неизвестно")
        art = item.get("supplierArticle", "Без артикула")
        name = item.get("subject", "Без предмета")
        qty = item.get("quantity", 0)
        if wh not in warehouse_data:
            warehouse_data[wh] = []
        warehouse_data[wh].append((art, name, qty))

    # --- Экспортируем по формату: "Склад", "Артикул", "Наименование", "Остаток"
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Склад", "Артикул", "Наименование", "Остаток"])
    for wh, products in warehouse_data.items():
        for idx, (art, name, qty) in enumerate(products):
            row = [
                wh if idx == 0 else "",
                art,
                name,
                qty
            ]
            writer.writerow(row)
    output.seek(0)
    csv_bytes = b'\xef\xbb\xbf' + output.getvalue().encode("utf-8")
    csv_file = BufferedInputFile(csv_bytes, filename="remains_report.csv")

    await callback.message.answer_document(
        document=csv_file,
        caption="🗂 Ваш отчёт по остаткам в формате CSV."
    )
    await progress_msg.edit_text("✅ CSV-отчёт отправлен!", parse_mode="HTML")
