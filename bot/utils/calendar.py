# utils/calendar.py

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, DialogCalendar, DialogCalendarCallback

# Календарь для выбора одной даты
def get_simple_calendar():
    return SimpleCalendar(locale="ru")  # Русская локализация

# Календарь для выбора диапазона дат (если понадобится)
def get_dialog_calendar():
    return DialogCalendar(locale="ru")
