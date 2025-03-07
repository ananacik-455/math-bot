from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.storage import phrases, save_user_data, load_user_data
from utils.logging_config import logger
from handlers.menu import show_main_menu
from handlers.book_lesson import book_start
from utils.messages import send_message_to_self
from handlers.tests import check_text_answer
from config import QUESTIONS


# === Зареєструвати на урок ===
async def register_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускає процес реєстрації на пробне заняття."""
    # Визначаємо джерело виклику (команда або кнопка)
    # user_id, username, message_context = None, "Без нікнейму", None
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    message_context = query.message
    # if update.callback_query:
    #     query = update.callback_query
    #     user_id = str(query.from_user.id)
    #     message_context = query.message
    #     await query.answer()
    # elif update.message:
    #     message = update.message
    #     user_id = str(message.from_user.id)
    #     message_context = message

    if not user_id or not message_context:
        return  # Вихід, якщо немає даних користувача або контексту повідомлення

    data = load_user_data(user_id)
    context.user_data["user_id"] = user_id
    if data["answers"]:
        # Користувач уже заповнював анкету
        answers = data["answers"]
        answers_text = "\n".join([f"{QUESTIONS[i]['question']} {answers[i]}" for i in range(len(answers))])

        keyboard = [
            [InlineKeyboardButton("Пройти знову", callback_data="retry_survey")],
            [InlineKeyboardButton("Перейти до запису на заняття", callback_data="skip_survey")],
            [InlineKeyboardButton("Головне меню", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = phrases["booking"]["filled_survey"]
        text = text.replace("answers_text", answers_text)
        await query.edit_message_text(
            text,
            reply_markup=reply_markup
        )
    else:
        # Якщо анкети немає, починаємо її проходження
        await start_survey(update, context)


async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE, first_message=True) -> None:
    """Розпочинає процес анкетування."""
    # Завантажуємо користувача, та стираємо відповіді
    user_id = context.user_data["user_id"]
    user_progress = load_user_data(user_id)
    user_progress["answers"] = []

    # Зберігаємо про користувача в context
    context.user_data["user_progress"] = user_progress
    if first_message:
        await context.bot.send_message(
            chat_id=user_id,
            text=phrases["booking"]["before_survey"]
        )
    await ask_question(update, context)


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Задає наступне питання користувачеві."""
    # Зчитуємо прогрес з контекст
    user_id = context.user_data["user_id"]
    progress = context.user_data["user_progress"]
    if progress and len(progress["answers"]) < len(QUESTIONS):
        question_data = QUESTIONS[len(progress["answers"])]
        context.user_data["user_progress"]["expected_type"] = question_data["type"]

        await context.bot.send_message(chat_id=user_id, text=question_data["question"])
    else:
        # Завершення анкети через зміни типу на НаН
        progress["expected_type"] = None
        context.user_data["user_id"] = user_id
        await save_user_data(user_id, progress)
        await context.bot.send_message(chat_id=user_id, text=phrases["booking"]["after_survey"])
        await book_start(update, context)


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє будь-які текстові повідомлення, але зберігає лише відповіді на анкету."""

    try:
        user_progress = context.user_data["user_progress"]
    except KeyError:
        print(f"Random text from {update.message.from_user.username}")
        return

    if user_progress == "QA":
        user = update.message.from_user
        message_text = update.message.text
        # Створюємо посилання на профіль користувача
        user_link = f"[ {user.full_name} ]( tg://user?id={user.id} ) ( @{user.username} )"

        # Формуємо повідомлення для вчителя
        teacher_message = f"📩 *Нове повідомлення від {user_link}:*\n\n{message_text}"
        await send_message_to_self(context.application, teacher_message)
        del context.user_data["user_progress"]
        return
    elif user_progress == "test":
        # Відповідь на тестове питання
        message_text = update.message.text
        context.user_data["user_answer"] = message_text
        del context.user_data["user_progress"]
        await check_text_answer(update, context)
        return

    user_id = context.user_data["user_id"]
    text = update.message.text.strip()

    if user_progress.get("expected_type"):
        # Якщо користувач проходить анкету, перевіряємо правильність відповіді
        expected_type = user_progress["expected_type"]

        if expected_type == "number" and not text.isdigit():
            await context.bot.send_message(chat_id=user_id, text="Будь ласка, введіть число.")
            return

        # Зберігаємо відповідь
        context.user_data["user_progress"]["answers"].append(text)

        # Перехід до наступного питання
        await ask_question(update, context)
    else:
        # Якщо користувач не проходить анкету, просто відповідаємо
        logger.warning(f"Отримано невідому команду від {update.effective_user.username}: {update.message.text}")
        await update.message.reply_text("Вибачте, я не розумію цю команду. Повертаємось в головне меню.")
        await context.bot.send_message(chat_id=user_id, text="Я поки не знаю, що з цим робити 😅")
        await show_main_menu(update, context)


async def handle_survey_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє рішення користувача щодо повторного проходження анкети."""
    query = update.callback_query

    if query.data == "retry_survey":
        await query.message.reply_text(phrases["booking"]["again_survey"])
        await start_survey(update, context, first_message=False)
    elif query.data == "skip_survey":
        await book_start(update, context)
        return
