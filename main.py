from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN
import handlers.menu as menu
import handlers.tests as tests
import handlers.book_lesson as book_lesson
import handlers.survey as survey
import handlers.others as others
from utils.logging_config import logger
from utils.messages import reply_to_student


# Ініціалізація бота
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Додавання обробників команд
application.add_handler(CommandHandler("start", menu.start))

# Головне меню
application.add_handler(CommandHandler("menu", menu.show_main_menu))
application.add_handler(CallbackQueryHandler(menu.show_main_menu, pattern="menu"))

# Інформація
application.add_handler(CallbackQueryHandler(menu.show_information_menu, pattern="information"))
application.add_handler(CallbackQueryHandler(menu.show_information_details, pattern=r"about_*"))

# Тестування
application.add_handler(CallbackQueryHandler(tests.show_tests, pattern="testing"))
# application.add_handler(CommandHandler("test", tests.show_tests))
application.add_handler(CallbackQueryHandler(tests.show_tests, pattern="show_tests"))
application.add_handler(CallbackQueryHandler(tests.show_test_info, pattern=r"info_.*"))
application.add_handler(CallbackQueryHandler(tests.start_test, pattern=r"start_.*"))
application.add_handler(CallbackQueryHandler(tests.check_answer, pattern=r"answer_.*"))

# Анкетування
application.add_handler(CallbackQueryHandler(survey.register_lesson, pattern="lesson_book"))
application.add_handler(CallbackQueryHandler(survey.register_lesson, pattern="register_lesson"))
application.add_handler(CallbackQueryHandler(survey.handle_survey_decision, pattern="retry_survey|skip_survey"))
# Обробник вибору в меню
# application.add_handler(CallbackQueryHandler(handle_menu_selection))

# Бронювання уроку
# application.add_handler(CommandHandler("schedule", survey.register_lesson))  # Викликаємо список годин
application.add_handler(CallbackQueryHandler(book_lesson.ask_for_day, pattern="ask_for_day"))
application.add_handler(CallbackQueryHandler(book_lesson.ask_for_time, pattern=r"day_.*"))
application.add_handler(CallbackQueryHandler(book_lesson.book_time, pattern=r"time_.*"))
application.add_handler(CallbackQueryHandler(book_lesson.change_lesson, pattern="^change_lesson$"))
application.add_handler(CallbackQueryHandler(book_lesson.cancel_lesson, pattern="^cancel_lesson$"))

# Питання вчителю
application.add_handler(CallbackQueryHandler(others.ask_me, pattern="qa"))

# Обробник невідомих команд
# application.add_handler(MessageHandler(filters.COMMAND, handle_unknown))
application.add_handler(MessageHandler(filters.REPLY, reply_to_student))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.REPLY, survey.handle_unknown))

# Запуск бота
if __name__ == "__main__":
    logger.info("✅ Бот запущено!")
    application.run_polling(stop_signals=["SIGINT", "SIGTERM"])
