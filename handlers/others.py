import pytz
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext
from config import ADMIN_ID
from datetime import datetime, timedelta
from utils.storage import phrases


async def ask_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запитує у користувача питання."""
    query = update.callback_query
    context.user_data["user_progress"] = "QA"
    await query.edit_message_text(phrases["ask_me"])


async def send_reminder(context: CallbackContext):
    """Функція, що відправляє нагадування"""
    job = context.job
    chat_id = job.chat_id
    lesson_time = job.data
    user_name = phrases[job.data["user_id"]]["username"]

    reminder_text = phrases["booking"]["reminder_text"]
    reminder_text.replace("lesson_time", lesson_time)

    # Надсилаємо нагадування учню
    await context.bot.send_message(chat_id=chat_id, text=reminder_text)

    # Надсилаємо нагадування тобі (вчителю)
    reminder_text_teacher = phrases["booking"]["text_teacher"]
    reminder_text_teacher = reminder_text_teacher.replace("user_name", user_name)
    reminder_text_teacher = reminder_text_teacher.replace("lesson_time", lesson_time)

    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 Учень {user_name} має урок о {lesson_time}!")


async def create_reminder(
        update,
        context,
        selected_date,
        selected_time,
        user_id,
        job_name,
        timedelta_min=30):
    # Плануємо нагадування за 30 хвилин до уроку
    kyiv_tz = pytz.timezone("Europe/Kyiv")
    start_datetime = kyiv_tz.localize(datetime.strptime(f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M"))
    reminder_time = start_datetime - timedelta(minutes=timedelta_min)

    context.job_queue.run_once(
        send_reminder,
        when=reminder_time,
        chat_id=user_id,
        name=job_name,
        data={"user_id": user_id, "selected_date": selected_date, "selected_time": selected_time}
    )


async def delete_reminder(update, context, job_name):
    current_jobs = context.job_queue.jobs()
    for job in current_jobs:
        if job.name == job_name:
            job.schedule_removal()
            break

# async def schedule_reminder(update, context, user_id, selected_date, selected_time):
#     """Заплановує повідомлення через 2 хв після бронювання."""
#     kyiv_tz = pytz.timezone("Europe/Kyiv")
#     current_time = datetime.now(kyiv_tz)
#     reminder_time = current_time + timedelta(minutes=2)
#
#     job_name = f"reminder_{user_id}_{selected_date}_{selected_time}"
#
#     context.job_queue.run_once(
#         send_reminder,
#         when=(reminder_time - current_time).total_seconds(),
#         chat_id=update.effective_chat.id,
#         name=job_name,
#         data={"user_id": user_id, "selected_date": selected_date, "selected_time": selected_time}
#     )
#
#
# async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
#     """Надсилає нагадування про урок користувачу та вчителю."""
#     job = context.job
#     user_id = job.data["user_id"]
#     selected_date = job.data["selected_date"]
#     selected_time = job.data["selected_time"]
#
#     message_text = f"🔔 Нагадування! Урок запланований на {selected_date} о {selected_time}."
#
#     # Надсилаємо повідомлення учню
#     await context.bot.send_message(chat_id=user_id, text=message_text)
#
#     # Надсилаємо повідомлення вчителю (замініть на свій Telegram ID)
#     await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 Учень записався: {message_text}")
