import json
import os
from utils.logging_config import logger
from config import DATA_FILE, TEST_FILE, default_dict

VARIATNS = ["А", "Б", "В", "Г", "Д"]

try:
    with open("data/telegram_bot_phrases.json", encoding="utf-8") as file:
        phrases = json.load(file)
        logger.info("JSON-файл успішно завантажено.")
except (FileNotFoundError, json.JSONDecodeError) as e:
    logger.error(f"Помилка завантаження JSON-файлу: {e}")
    raise ValueError("Помилка завантаження JSON-файлу. Перевірте файл.") from e


async def save_user_data(user_id: str, user_progress: dict) -> None:
    """Зберігає анкету користувача у JSON-файл."""
    data = load_user_data(user_id, full=True)
    data[user_id] = user_progress

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_user_data(user_id: str, full=False) -> dict:
    """Завантажує дані користувачів з файлу."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            try:
                if full:
                    return json.load(file)
                return json.load(file)[user_id]
            except (json.JSONDecodeError, KeyError):
                return default_dict
    return default_dict


def load_test_data()-> dict:
    """Завантажує дані тесту."""
    if os.path.exists(TEST_FILE):
        try:
            with open(TEST_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, KeyError):
            logger.info(f"Can't open {TEST_FILE}")


if __name__=="__main__":
    print(load_user_data('969050443'))