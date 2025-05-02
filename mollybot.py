import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = '7628456508:AAF1Th7JejBs2u3YYsD4vfxtqra5PmM8c14'

# Личность бота
PERSONALITY = {
    'name': 'Молли',
    'age': 22,
    'occupation': 'студентка',
    'hobbies': ['музыка', 'рисование', 'программирование'],
    'personality_traits': ['дружелюбная', 'умная', 'творческая'],
    'communication_style': 'дружеский и поддерживаемый'
}

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Привет! Я {PERSONALITY['name']}, {PERSONALITY['age']} лет, {PERSONALITY['occupation']}.\n"
        "Я всегда готова помочь и поддержать тебя.\n"
        "\n"
        "Доступные команды:\n"
        "/help - помощь\n"
        "/about - обо мне"
    )

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я Молли, твой дружелюбный AI-собеседник.\n"
        "Я всегда готова помочь и поддержать тебя.\n"
        "\n"
        "Доступные команды:\n"
        "/help - помощь\n"
        "/about - обо мне"
    )

# Обработчик команды /about
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Я {PERSONALITY['name']}, {PERSONALITY['age']} лет, {PERSONALITY['occupation']}.\n"
        f"Мои хобби: {', '.join(PERSONALITY['hobbies'])}\n"
        f"Черты моего характера: {', '.join(PERSONALITY['personality_traits'])}\n"
        f"Я общаюсь в стиле: {PERSONALITY['communication_style']}"
    )

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    
    # Отправляем сообщение о том, что обрабатываем запрос
    await update.message.reply_text("Привет! Я обрабатываю ваш запрос. Пожалуйста, подождите немного.")
    
    try:
        # Простой ответ на сообщение
        response = f"Я поняла: {user_message}\n" \
                   "Я всегда готова помочь и поддержать тебя!"
        
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        await update.message.reply_text("Извините, произошла ошибка при обработке вашего сообщения. Попробуйте позже.")

# Основная функция
def main():
    try:
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Бот запущен и готов к работе!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
        raise

if __name__ == '__main__':
    main()