import csv
import io
from aiogram.types.input_file import BufferedInputFile

def export_to_csv(items: list, columns: list, filename: str = "report.csv"):
    """
    Генерирует BufferedInputFile с CSV по переданным данным.
    :param items: список словарей или списков
    :param columns: список названий колонок (и ключей для словаря)
    :param filename: имя файла
    :return: BufferedInputFile для Telegram (aiogram v3+)
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(columns)
    for row in items:
        if isinstance(row, dict):
            writer.writerow([row.get(col, "") for col in columns])
        else:
            writer.writerow(row)
    output.seek(0)
    csv_bytes = b'\xef\xbb\xbf' + output.getvalue().encode("utf-8")
    return BufferedInputFile(csv_bytes, filename)
