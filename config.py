import os

from dotenv import load_dotenv

from utils.logging_config import logger

load_dotenv(dotenv_path="data\.env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
DATA_FILE = "data/students_data.json"
TEST_FILE = "data/test_info.json"

# Креденшіали на Google Calendar API
SERVICE_ACCOUNT_FILE = "data/credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = "karasina1337@gmail.com"

default_dict = {"username": None,
                "answers": [],
                "lesson": dict()}

# Питання анкети
# TODO: змінити питання
QUESTIONS = [
    {"question": "Як тебе звати?", "type": "text"},
    {"question": "Скільки тобі років?", "type": "number"},
    {"question": "Як оцінюєш свої знання з математики?", "type": "text"}
]


if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN не знайдено у файлі .env")
    raise ValueError("❌ TELEGRAM_TOKEN не знайдено у файлі .env")

if not os.path.exists(DATA_FILE):
    logger.error("DATA_FILE не знайдено")
    raise ValueError("❌ DATA_FILE не знайдено")

