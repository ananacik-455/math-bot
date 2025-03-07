import os
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.storage import phrases, load_test_data, VARIATNS
from handlers.menu import show_main_menu
from utils.storage import load_user_data, save_user_data
from utils.logging_config import logger


async def show_tests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /test - Показує доступні тести"""
    keyboard = [[InlineKeyboardButton(test, callback_data=f"info_{test}")] for test in phrases["test"]["test_variants"]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text("Оберіть тест:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Оберіть тест:", reply_markup=reply_markup)


async def show_test_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показує інформацію про тест і варіанти дій"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    test_name = query.data.split("_")[1]

    keyboard = [
        [InlineKeyboardButton("Розпочати тест", callback_data=f"start_{test_name}")],
        [InlineKeyboardButton("Обрати інший", callback_data="show_tests")],
        [InlineKeyboardButton("Головне меню", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        marks = load_user_data(str(user_id))["test"]
        test_score = marks[test_name]
    except KeyError:
        logger.info(f"User {user_id} haven't solve {test_name} test.")
        test_score = None

    test = load_test_data()[test_name]
    context.user_data["test"] = test
    text = phrases['test']['test_variants'][test_name]
    # Зміна тексту
    text = text.replace("test_length", str(test["len_test"]))
    if test_score:
        text += f"\n\n Ви вже проходили цей тест. Ваш попередній результат: {test_score}. Та ви можете його покращити 🧠"

    await query.edit_message_text(f"{text}\n\n"
                                  f"Що хочете зробити?",
                                  reply_markup=reply_markup)


async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Початок вибраного тесту"""
    query = update.callback_query
    await query.answer()

    test_name = query.data.split("_")[-1]
    test = context.user_data["test"]

    # Генеруємо питаня з випадковим порядком
    questions = random.sample(test["questions"], k=int(test["len_test"]))
    random.shuffle(questions)

    # Зберігаємо стан тесту
    context.user_data["folder_path"] = test["folder_path"]
    context.user_data["current_test"] = test_name
    context.user_data["len_question"] = test["len_question"]
    context.user_data["questions"] = questions
    context.user_data["current_index"] = 0
    context.user_data["score"] = 0  # Лічильник правильних відповідей

    await query.edit_message_text(f"{phrases['test']['test_variants'][test_name]}\n\n"
                                  f"Готуйтеся! Починаємо тест.")
    await send_question(update, context)


async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Відправляє поточне питання користувачу"""
    query = update.callback_query if update.callback_query else None
    message = update.message if update.message else None
    user_id = query.from_user.id if query else message.from_user.id

    questions = context.user_data.get("questions", [])
    current_index = context.user_data.get("current_index", 0)

    if current_index >= len(questions):
        await update.effective_chat.send_message(
            f"🎉 Тест завершено!\nВаш результат: {context.user_data['score']}/{len(questions)}"
        )

        # Save test result to DB
        user_data = load_user_data(str(user_id))
        if "test" not in user_data:
            user_data["test"] = {}  # Initialize the 'test' dictionary if it doesn't exist

        user_data["test"][context.user_data["current_test"]] = f"{context.user_data['score']}/{len(questions)}"
        await save_user_data(str(user_id), user_data)

        await show_main_menu(update, context, new=True)
        return

    question = questions[current_index]
    context.user_data["correct_answer"] = question["correct_answer"]

    # await context.bot.send_message(user_id, f"Питання № {current_index + 1}")

    # Відправка питання
    question_path = os.path.join(context.user_data["folder_path"], f"task_{question['id']}.png")
    with open(question_path, "rb") as photo:
        await context.bot.send_photo(user_id, photo, caption=f"Питання №{current_index + 1}\n{question['description']}")

    # Генерація варіантів відповіді
    if question["question_type"] == "one_choice":
        keyboard = [[InlineKeyboardButton(variant, callback_data=f"answer_{variant}")]
                    for variant in VARIATNS[:context.user_data["len_question"]]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_chat.send_message("⬇ Оберіть відповідь:", reply_markup=reply_markup)

    elif question["question_type"] == "text":
        context.user_data["user_progress"] = "test"
        await update.effective_chat.send_message("⬇ Напишіть вашу відповідь:")


async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Перевіряє відповідь користувача"""
    query = update.callback_query
    await query.answer()

    selected_answer = query.data.split("_")[1]
    correct_answer = context.user_data["correct_answer"]

    # if selected_answer == context.user_data["correct_answer"]:
    #     await update.effective_chat.send_message("✅ Правильно!")
    #     context.user_data["score"] += 1
    # else:
    #     await update.effective_chat.send_message("❌ Невірно!")
    #
    # context.user_data["current_index"] += 1
    # await send_question(update, context)

# Перевірка відповіді
    if selected_answer == correct_answer:
        result_text = "✅ Правильно!"
        context.user_data["score"] += 1
    else:
        result_text = f"❌ Невірно! Твоя відповідь: {selected_answer}"

    # Видаляємо старі варіанти відповідей
    await context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=result_text
    )

    # Переходимо до наступного питання
    context.user_data["current_index"] += 1
    await send_question(update, context)


async def check_text_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_answer = context.user_data["user_answer"]
    correct_answer = context.user_data["correct_answer"]

    if selected_answer == correct_answer:
        await update.effective_chat.send_message("✅ Правильно!")
        context.user_data["score"] += 1
    else:
        await update.effective_chat.send_message("❌ Невірно!")

    context.user_data["current_index"] += 1
    await send_question(update, context)
