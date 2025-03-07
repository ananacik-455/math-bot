from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils.storage import phrases
from utils.logging_config import logger
from utils.messages import send_message_to_self


# === Основні команди ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Відправляє вітальне повідомлення і головне меню."""
    msg = f"Команда /start отримана від {update.effective_user.username} ({update.effective_user.id})"
    logger.info(msg)
    await send_message_to_self(context.application, msg)
    await update.message.reply_text(phrases["greeting"]["welcome_message"])
    await show_main_menu(update, context)


# === Головне меню ===
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, new=False) -> None:
    """Показ головного меню."""
    keyboard = [[InlineKeyboardButton(option, callback_data=callback_data)] for option, callback_data in phrases["menu"]["options"].items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if new:
        await update.effective_chat.send_message(
            phrases["menu"]["description"], reply_markup=reply_markup
        )
    else:
        if update.callback_query:
            await update.callback_query.edit_message_text(phrases["menu"]["description"], reply_markup=reply_markup)
        else:
            await update.message.reply_text(phrases["menu"]["description"], reply_markup=reply_markup)


# === Функції підменю ===
async def show_information_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показує меню 'Інформація'."""
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton(name, callback_data=callback)] for name, callback in phrases["info"]["menu"].items()]
    keyboard.append([InlineKeyboardButton("Головне меню", callback_data="menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Що саме вас цікавить?", reply_markup=reply_markup)


async def show_information_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показувати інформацію про викладача, методи навчання або уроки."""
    query = update.callback_query
    await query.answer()

    selection = query.data

    info_texts = phrases["info"]["options"]

    text = info_texts.get(selection, "Вибачте, ця опція недоступна.")
    keyboard = [[InlineKeyboardButton("Назад", callback_data="information")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup)
