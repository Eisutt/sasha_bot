from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import datetime

def create_calendar(year=None, month=None):
    now = datetime.datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    keyboard = []

    # Шапка с месяцем и годом
    row = [InlineKeyboardButton(f'{datetime.date(year, month, 1):%B %Y}', callback_data='IGNORE')]
    keyboard.append(row)

    # Названия дней недели
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    row = [InlineKeyboardButton(day, callback_data="IGNORE") for day in days]
    keyboard.append(row)

    month_calendar = build_calendar_matrix(year, month)

    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="IGNORE"))
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                row.append(InlineKeyboardButton(str(day), callback_data=f"CALENDAR_{date_str}"))
        keyboard.append(row)

    # Стрелочки
    row = [
        InlineKeyboardButton("<", callback_data=f"PREV-MONTH_{year}_{month}"),
        InlineKeyboardButton(">", callback_data=f"NEXT-MONTH_{year}_{month}")
    ]
    keyboard.append(row)

    return InlineKeyboardMarkup(keyboard), None

def build_calendar_matrix(year, month):
    import calendar
    calendar.setfirstweekday(calendar.MONDAY)
    month_calendar = calendar.monthcalendar(year, month)
    return month_calendar

def process_calendar_selection(update: Update, context):
    query = update.callback_query
    data = query.data

    if data.startswith("CALENDAR_"):
        date_str = data.replace("CALENDAR_", "")
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True, date

    elif data.startswith("PREV-MONTH_") or data.startswith("NEXT-MONTH_"):
        parts = data.split("_")
        year, month = int(parts[1]), int(parts[2])

        if "PREV" in data:
            month -= 1
            if month < 1:
                month = 12
                year -= 1
        else:
            month += 1
            if month > 12:
                month = 1
                year += 1

        new_calendar, _ = create_calendar(year, month)
        query.edit_message_reply_markup(reply_markup=new_calendar)
        return False, None

    return False, None
