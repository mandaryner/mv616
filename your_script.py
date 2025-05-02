# your_script.py
import logging
from telegram import Update
from telegram.ext import CommandHandler, Application

# Установим уровень логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Обработчик команды /start
async def start(update: Update, context):
    """Обработчик команды /start"""
    await update.message.reply_text('Привет! Я бот!')

# Основная функция для запуска бота
def main():
    """Запуск бота"""
    # Вставьте сюда ваш токен бота
    bot_token = '7628456508:AAF1Th7JejBs2u3YYsD4vfxtqra5PmM8c14'

    # Создаем объект Application
    application = Application.builder().token(bot_token).build()

    # Регистрируем обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
