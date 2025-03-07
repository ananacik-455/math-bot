from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from google_calendar import get_next_7_days, get_available_times
from utils.storage import load_user_data, save_user_data
from datetime import datetime, timedelta
import pytz
from google_calendar import create_event_from_calendar, delete_event_from_calendar
from handlers.others import delete_reminder, create_reminder
from handlers.menu import show_main_menu


# === Бронювання уроку ===
async def ask_for_day(update, context):
    """Отримує список вільних слотів та пропонує їх користувачеві."""
    days = get_next_7_days()
    keyboard = [[InlineKeyboardButton(day, callback_data=f"day_{idx}")] for idx, day in enumerate(days)]
    keyboard.extend([[InlineKeyboardButton("Головне меню", callback_data=f"menu")]])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text("Оберіть зручний день для заняття:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Оберіть зручний день для заняття:", reply_markup=reply_markup)


async def ask_for_time(update, context):
    """Пропонує вибір вільного часу у вибраний день."""
    query = update.callback_query
    await query.answer()

    selected_day_idx = int(query.data.split("_")[1])
    selected_date = datetime.now(pytz.utc) + timedelta(days=selected_day_idx + 1)
    selected_date = selected_date.date()  # Беремо лише дату без часу
    context.user_data["selected_date"] = selected_date  # Зберігаємо дату у контексті

    available_times = get_available_times(selected_date)

    keyboard = [[InlineKeyboardButton(time, callback_data=f"time_{time}")] for time in available_times]
    keyboard.extend([[InlineKeyboardButton("Обрати інший день", callback_data=f"ask_for_day")]])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(f"Ви обрали {get_next_7_days()[selected_day_idx]}.\nОберіть час:",
                                                      reply_markup=reply_markup)
    else:
        await update.message.reply_text(f"Ви обрали {get_next_7_days()[selected_day_idx]}.\nОберіть час:",
                                        reply_markup=reply_markup)


async def book_start(update, context):
    """Бронює вибраний час у Google Календарі."""

    user_id = str(context.user_data["user_id"])
    students_data = load_user_data(user_id)

    # Перевіряємо, чи користувач вже записаний
    if students_data["lesson"]:

        booked_lesson = students_data["lesson"]
        keyboard = [
            [InlineKeyboardButton("Записатися на інший час", callback_data="change_lesson")],
            [InlineKeyboardButton("Відмінити заняття", callback_data="cancel_lesson")],
            [InlineKeyboardButton("Головне меню", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"Ви вже записані на {booked_lesson['date']} о {booked_lesson['time']} 🗓\n\n" \
               f"Ви можете змінити або скасувати запис:"

        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
        return
    await ask_for_day(update, context)
    return


async def book_time(update, context):
    """Записуємо на обраний час"""
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    students_data = load_user_data(user_id)

    selected_time = query.data.split("_")[1].split(" ")[0]
    selected_date = context.user_data.get("selected_date")
    username = query.from_user.username or "Без нікнейму"

    # Створити нагадування юзеру
    await create_reminder(
        update,
        context,
        selected_date=selected_date,
        selected_time=selected_time,
        user_id=user_id,
        job_name=f"reminder_{user_id}_{selected_time}"
    )

    # Створення івенту в календарі
    # TODO: додати пошту користувача, якщо він її ввів.
    # TODO: При перезапуску бота створити всі нагадування знову (Можливо треба переписати функцію)
    event_id = create_event_from_calendar(selected_time, selected_date, username)

    # Додаємо username до учня
    if not students_data["username"]:
        students_data["username"] = username

    # Додаємо інформацію про пробне заняття
    students_data["lesson"] = {
        "date": str(selected_date),
        "time": selected_time,
        "event_id": event_id,  # Додаємо ID події
    }
    await save_user_data(user_id, students_data)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"Готово! Ви записані на заняття {selected_date} о {selected_time} 🗓")
    else:
        await update.message.reply_text(f"Готово! Ви записані на заняття {selected_date} о {selected_time} 🗓")
    await show_main_menu(update, context, new=True)
    return


async def change_lesson(update, context):
    """Перезаписує користувача на новий час, спочатку видаляючи старе заняття."""
    query = update.callback_query
    await query.answer()

    await cancel_lesson(update, context)
    await ask_for_day(update, context)


async def cancel_lesson(update, context):
    """Обробляє скасування записаного заняття."""
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    students_data = load_user_data(user_id)

    await delete_reminder(
        update,
        context,
        job_name=f"reminder_{user_id}_{students_data['lesson']['time']}")

    # Видаляю з календаря подію
    delete_event_from_calendar(students_data["lesson"]["event_id"])

    # Видаляю запис з бази
    students_data["lesson"] = {}
    await save_user_data(user_id, students_data)

    await query.edit_message_text("Ваш запис було успішно скасовано ❌")
    await show_main_menu(update, context, new=True)
