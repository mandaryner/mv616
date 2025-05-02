# your_script.py
import logging
from telegram import Bot
from telegram.ext import CommandHandler, Updater

# Установим уровень логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Обработчик команды /start
def start(update, context):
    """Обработчик команды /start"""
    update.message.reply_text('Привет! Я бот!')

# Основная функция для запуска бота
def main():
    """Запуск бота"""
    # Вставьте сюда ваш токен бота
    bot_token = 'ВАШ_ТОКЕН_ЗДЕСЬ'

    # Создаем объект Updater и получаем диспетчера
    updater = Updater(bot_token)

    # Получаем диспетчера для добавления обработчиков
    dispatcher = updater.dispatcher

    # Регистрируем обработчик команды /start
    dispatcher.add_handler(CommandHandler("start", start))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
