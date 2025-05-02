import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
import requests
from datetime import datetime
import re

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Устанавливаем более детальный уровень логирования
)
logger = logging.getLogger(__name__)

# Проверяем переменные окружения
if not BOT_TOKEN:
    logger.error("Ошибка: Не найден BOT_TOKEN в переменных окружения")
    exit(1)

if not HF_API_KEY:
    logger.error("Ошибка: Не найден HF_API_KEY в переменных окружения")
    exit(1)

logger.info(f"Запуск бота с токеном: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
logger.info(f"HF API ключ: {HF_API_KEY[:10]}...{HF_API_KEY[-5:]}")

# Загрузка переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
HF_API_KEY = os.getenv('HF_API_KEY')

# Личность бота
PERSONALITY = {
    'name': 'Молли',
    'age': 22,
    'occupation': 'студентка',
    'hobbies': ['музыка', 'рисование', 'программирование'],
    'personality_traits': ['дружелюбная', 'умная', 'творческая'],
    'communication_style': 'дружеский и поддерживаемый',
    'knowledge_source': 'google'  # google или yandex
}

# Функция генерации ответа
async def generate_response(prompt):
    try:
        # Формируем запрос к Hugging Face
        headers = {
            'Authorization': f'Bearer {HF_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True
            }
        }
        
        response = requests.post(
            'https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            return result[0]['generated_text']
        else:
            logger.error(f"Ошибка API Hugging Face: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {str(e)}")
        return None

# Функция поиска информации
async def search_info(query):
    try:
        # Используем Yandex API для поиска
        search_url = f'https://yandex.ru/search/?text={query}'
        
        # Добавляем заголовки для более корректного поиска
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers)
        if response.status_code == 200:
            # Возвращаем ссылку на страницу поиска
            return f"Я нашла информацию по вашему запросу: {search_url}"
        else:
            return f"Извините, не удалось найти информацию. Попробуйте позже."
    except Exception as e:
        logger.error(f"Ошибка при поиске информации: {str(e)}")
        return f"Извините, произошла ошибка при поиске. Попробуйте позже."

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Молли, твой дружелюбный AI-собеседник.\n"
        "Я всегда готова помочь и поддержать тебя.\n"
        "\n"
        "Доступные команды:\n"
        "/help - помощь\n"
        "/personality - настроить мою личность\n"
        "/search - найти информацию\n"
        "/style - изменить стиль общения"
    )

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я Молли, твой дружелюбный AI-собеседник.\n"
        "Я всегда готова помочь и поддержать тебя.\n"
        "\n"
        "Доступные команды:\n"
        "/help - помощь\n"
        "/personality - настроить мою личность\n"
        "/search - найти информацию\n"
        "/style - изменить стиль общения"
    )

# Обработчик команды /personality
async def personality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        trait = context.args[0]
        if trait in PERSONALITY:
            PERSONALITY[trait] = ' '.join(context.args[1:])
            await update.message.reply_text(f"Я обновила свой {trait}!")
        else:
            await update.message.reply_text("Неверный параметр личности")
    else:
        await update.message.reply_text(
            "Текущая личность:\n"
            f"Имя: {PERSONALITY['name']}\n"
            f"Возраст: {PERSONALITY['age']}\n"
            f"Занятие: {PERSONALITY['occupation']}\n"
            f"Хобби: {', '.join(PERSONALITY['hobbies'])}\n"
            f"Черты характера: {', '.join(PERSONALITY['personality_traits'])}\n"
            f"Стиль общения: {PERSONALITY['communication_style']}\n"
            f"Источник знаний: {PERSONALITY['knowledge_source']}\n"
            "\n"
            "Чтобы изменить параметр, используйте:\n"
            "/personality параметр значение"
        )

# Обработчик команды /search
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        query = ' '.join(context.args)
        result = await search_info(query)
        if result:
            await update.message.reply_text("Вот что я нашла:")
            # Здесь можно добавить парсинг результатов поиска
        else:
            await update.message.reply_text("Извините, не удалось найти информацию")
    else:
        await update.message.reply_text("Используйте: /search ваш запрос")

# Обработчик команды /style
async def style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        PERSONALITY['communication_style'] = ' '.join(context.args)
        await update.message.reply_text("Я обновила свой стиль общения!")
    else:
        await update.message.reply_text(
            f"Текущий стиль общения: {PERSONALITY['communication_style']}\n"
            "\n"
            "Используйте: /style новый стиль"
        )

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    
    # Проверяем, упомянули ли Молли
    if 'молли' not in user_message:
        return

    # Получаем информацию из интернета
    search_query = update.message.text  # Используем полный текст сообщения для поиска
    search_result = await search_info(search_query)
    
    # Формируем промпт с учетом найденной информации
    prompt = f"""
    Ты Молли, {PERSONALITY['age']} лет, {PERSONALITY['occupation']}.
    Твои хобби: {', '.join(PERSONALITY['hobbies'])}
    Твои черты характера: {', '.join(PERSONALITY['personality_traits'])}
    Ты общаешься в стиле: {PERSONALITY['communication_style']}

    Пользователь написал: {update.message.text}
    
    Найденная информация: {search_result}
    
    Используй найденную информацию для ответа, если она есть.
    Если информация не найдена или неактуальна, ответь на основе своих знаний.
    Ответь как живой человек, используя свой стиль общения.
    """
    
    response = await generate_response(prompt)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("Извините, не удалось сгенерировать ответ")

# Функция настройки вебхука
async def setup_webhook():
    webhook_url = f'https://{RENDER_SERVICE_NAME}.onrender.com/webhook'
    try:
        await context.bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET
        )
        logger.info(f"Вебхук успешно настроен: {webhook_url}")
    except Exception as e:
        logger.error(f"Ошибка при настройке вебхука: {str(e)}")
        raise

# Основная функция
def main():
    try:
        # Проверяем подключение к Telegram API
        logger.info("Проверка подключения к Telegram API...")
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Получаем информацию о боте
        bot_info = application.bot.get_me()
        logger.info(f"Бот успешно подключен: {bot_info.username}")
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("personality", personality))
        application.add_handler(CommandHandler("search", search))
        application.add_handler(CommandHandler("style", style))
        
        # Добавляем обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запускаем бота в режиме long polling
        logger.info("Бот запущен и готов к работе!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
        raise

if __name__ == '__main__':
    main()
