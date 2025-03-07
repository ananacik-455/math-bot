import os
import json
import locale
from datetime import datetime, time, timedelta
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import SERVICE_ACCOUNT_FILE, SCOPES, CALENDAR_ID

locale.setlocale(locale.LC_ALL, "uk_UA.utf8") # Українська мова


# Авторизація через сервісний аккаунт
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("calendar", "v3", credentials=credentials)


# Функція для отримання 7 днів
def get_next_7_days():
    today = datetime.now(pytz.utc)
    return [(today + timedelta(days=i)).strftime("%A (%d.%m)").capitalize() for i in range(1, 8)]


# Функція для отримання вільних слотів у Google Calendar
def get_available_times(selected_date):
    kyiv_tz = pytz.timezone("Europe/Kyiv")

    start_of_day = kyiv_tz.localize(datetime.combine(selected_date, datetime.min.time()))
    end_of_day = kyiv_tz.localize(datetime.combine(selected_date, datetime.max.time()))

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])
    busy_slots = set()  # Використовуємо множину, щоб уникнути дублікатів

    for event in events:
        start_dt = datetime.fromisoformat(event["start"]["dateTime"]).astimezone(kyiv_tz)
        end_dt = datetime.fromisoformat(event["end"]["dateTime"]).astimezone(kyiv_tz)

        start_hour = start_dt.hour
        end_hour = end_dt.hour

        # Якщо подія завершується не рівно на годині, округляємо вгору
        if end_dt.minute > 0:
            end_hour += 1

        busy_slots.update(range(start_hour, end_hour))  # Додаємо зайняті години

    all_slots = set(range(9, 21))  # Доступні години 9:00 - 20:00
    free_slots = sorted(all_slots - busy_slots)  # Вільні слоти - ті, що не зайняті

    return [f"{hour}:00 - {hour}:55" for hour in free_slots]


def delete_event_from_calendar(event_id):
    """Видаляє подію з Google Календаря за її ID."""
    try:
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
        return True
    except Exception as e:
        print(f"Помилка при видаленні події: {e}")
        return False


def create_event_from_calendar(selected_time, selected_date, username):
    kyiv_tz = pytz.timezone("Europe/Kyiv")
    start_datetime = kyiv_tz.localize(datetime.strptime(f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M"))
    end_datetime = start_datetime + timedelta(minutes=55)

    event = {
        "summary": f"Пробне заняття - {username}",
        "start": {"dateTime": start_datetime.isoformat(), "timeZone": "Europe/Kyiv"},
        "end": {"dateTime": end_datetime.isoformat(), "timeZone": "Europe/Kyiv"},
    }

    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return created_event["id"]



if __name__ == "__main__":
    selected_date = datetime.now(pytz.utc) + timedelta(days=2 + 1)
    print(get_available_times(selected_date))