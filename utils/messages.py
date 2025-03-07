from telegram import Update
from telegram.ext import ContextTypes
import re
from config import ADMIN_ID
from utils.logging_config import logger


async def send_message_to_self(application, message: str) -> None:
    """Надсилає повідомлення адміністратору."""
    await application.bot.send_message(chat_id=ADMIN_ID, text=message)
    logger.info("Повідомлення адміністратору відправлено!")


async def reply_to_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Відповідає учню, якщо вчитель відповідає на його повідомлення в чаті з ботом."""
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Вам потрібно відповісти на повідомлення, яке бот переслав від учня.")
        return

    original_message = update.message.reply_to_message
    student_id = extract_user_id_from_message(original_message.caption or original_message.text)

    if not student_id:
        await update.message.reply_text("⚠️ Не вдалося знайти ID учня.")
        return

    # Отримуємо текст оригінального питання
    original_text = original_message.caption or original_message.text or "📩 (Медіафайл)"
    original_text = extract_user_question(original_text)

    response_text = f"📢 *Ваше питання:*\n_{original_text}_\n\n📩 *Відповідь вчителя:*"

    # Відповідаємо відповідним форматом
    if update.message.sticker:
        await context.bot.send_message(chat_id=student_id, text=response_text, parse_mode="Markdown")
        await context.bot.send_sticker(chat_id=student_id, sticker=update.message.sticker.file_id)

    elif update.message.photo:
        await context.bot.send_photo(chat_id=student_id, photo=update.message.photo[-1].file_id, caption=response_text,
                                     parse_mode="Markdown")

    elif update.message.video:
        await context.bot.send_video(chat_id=student_id, video=update.message.video.file_id, caption=response_text,
                                     parse_mode="Markdown")

    elif update.message.voice:
        await context.bot.send_message(chat_id=student_id, text=response_text, parse_mode="Markdown")
        await context.bot.send_voice(chat_id=student_id, voice=update.message.voice.file_id)

    elif update.message.document:
        await context.bot.send_document(chat_id=student_id, document=update.message.document.file_id,
                                        caption=response_text, parse_mode="Markdown")

    elif update.message.text:
        await context.bot.send_message(chat_id=student_id, text=f"{response_text}\n\n_{update.message.text}_",
                                       parse_mode="Markdown")

    await update.message.reply_text("✅ Відповідь надіслана учневі!")


def extract_user_id_from_message(text):
    """Витягує ID учня з пересланого ботом повідомлення."""
    match = re.search(r'tg://user\?id=(\d+)', text)
    return match.group(1) if match else None


def extract_user_question(message_text):
    match = re.search(r"\n\n(.+)", message_text, re.DOTALL)
    if match:
        return match.group(1).strip()
