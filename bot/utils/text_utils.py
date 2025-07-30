# utils/text_utils.py

import re

def normalize_warehouse_name(name: str) -> str:
    """
    Приводит название склада к унифицированному виду для корректного сравнения.
    Удаляет лишние слова, приводит к нижнему регистру, убирает спецсимволы и пробелы.
    """
    if not name:
        return ""
    name = name.lower()
    name = name.replace("ё", "е")
    # Удаляем часто встречающиеся "мусорные" слова
    remove_words = [
        "склад продавца", "склад", "центр обработки", "центр", "wb", "wildberries",
        "логистический", "комплекс", "отделение", " ", "-", "_"
    ]
    for word in remove_words:
        name = name.replace(word, "")
    # Оставляем только буквы и цифры
    name = re.sub(r'[^a-zа-я0-9]', '', name)
    return name.strip()

def is_positive_float(d: dict, key: str) -> bool:
    """
    Проверяет, что значение по ключу в словаре d является положительным числом (float > 0).
    Возвращает True, если да, иначе False.
    """
    try:
        return float(d.get(key, 0)) > 0
    except (TypeError, ValueError):
        return False
