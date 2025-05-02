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

# API ключ Hugging Face
HF_API_KEY = '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'

# Личность бота
PERSONALITY = {
    'name': 'Молли',
    'age': 22,
    'occupation': 'студентка',
    'hobbies': ['музыка', 'рисование', 'программирование'],
    'personality_traits': ['дружелюбная', 'умная', 'творческая'],
    'communication_style': 'дружеский и поддерживаемый'
}

# Функция для редактирования личности
async def edit_personality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        # Если нет аргументов, показываем текущую личность
        await update.message.reply_text(
            "Текущая личность:\n"
            f"Имя: {PERSONALITY['name']}\n"
            f"Возраст: {PERSONALITY['age']}\n"
            f"Занятие: {PERSONALITY['occupation']}\n"
            f"Хобби: {', '.join(PERSONALITY['hobbies'])}\n"
            f"Черты характера: {', '.join(PERSONALITY['personality_traits'])}\n"
            f"Стиль общения: {PERSONALITY['communication_style']}\n"
            "\n"
            "Чтобы изменить параметр, используйте:\n"
            "/edit name новое_имя\n"
            "/edit age новый_возраст\n"
            "/edit occupation новое_занятие\n"
            "/edit hobbies новое_хобби1,новое_хобби2\n"
            "/edit traits новая_черта1,новая_черта2\n"
            "/edit style новый_стиль"
        )
        return
    
    # Проверяем, что есть параметр и значение
    if len(context.args) < 2:
        await update.message.reply_text("Ошибка: Недостаточно параметров. Используйте /edit параметр значение")
        return
    
    parameter = context.args[0].lower()
    value = ' '.join(context.args[1:])
    
    # Обрабатываем разные параметры
    if parameter == 'name':
        PERSONALITY['name'] = value
    elif parameter == 'age':
        try:
            PERSONALITY['age'] = int(value)
        except ValueError:
            await update.message.reply_text("Ошибка: Возраст должен быть числом")
            return
    elif parameter == 'occupation':
        PERSONALITY['occupation'] = value
    elif parameter == 'hobbies':
        PERSONALITY['hobbies'] = value.split(',')
    elif parameter == 'traits':
        PERSONALITY['personality_traits'] = value.split(',')
    elif parameter == 'style':
        PERSONALITY['communication_style'] = value
    else:
        await update.message.reply_text("Ошибка: Неверный параметр. Доступные параметры: name, age, occupation, hobbies, traits, style")
        return
    
    await update.message.reply_text(f"Я обновила свой {parameter}!")

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
        "/about - обо мне\n"
        "/edit - редактировать мою личность"
    )

# Обработчик команды /about
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Я {PERSONALITY['name']}, {PERSONALITY['age']} лет, {PERSONALITY['occupation']}.\n"
        f"Мои хобби: {', '.join(PERSONALITY['hobbies'])}\n"
        f"Черты моего характера: {', '.join(PERSONALITY['personality_traits'])}\n"
        f"Я общаюсь в стиле: {PERSONALITY['communication_style']}"
    )

# Функция генерации ответа через Hugging Face
async def generate_response(prompt):
    try:
        # Логируем запрос
        logger.info(f"Отправляю запрос к Hugging Face с текстом: {prompt[:100]}...")
        
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
        
        # Попытка отправки запроса с таймаутом
        try:
            response = requests.post(
                'https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf',
                headers=headers,
                json=data,
                timeout=30  # Устанавливаем таймаут в 30 секунд
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Получен успешный ответ от Hugging Face")
                return result[0]['generated_text']
            else:
                logger.error(f"Ошибка API Hugging Face: {response.text}")
                logger.error(f"Код ошибки: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error("Время ожидания ответа истекло")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при отправке запроса: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {str(e)}")
        return None

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()
    
    # Отправляем сообщение о том, что обрабатываем запрос
    await update.message.reply_text("Привет! Я обрабатываю ваш запрос. Пожалуйста, подождите немного.")
    
    try:
        # Формируем промпт для нейросети
        prompt = f"""
        Ты {PERSONALITY['name']}, {PERSONALITY['age']} лет, {PERSONALITY['occupation']}.
        Твои хобби: {', '.join(PERSONALITY['hobbies'])}
        Твои черты характера: {', '.join(PERSONALITY['personality_traits'])}
        Ты общаешься в стиле: {PERSONALITY['communication_style']}

        Пользователь написал: {update.message.text}
        
        Ответь как живой человек, используя свой стиль общения.
        """
        
        # Генерируем ответ через Hugging Face
        response = await generate_response(prompt)
        if response:
            # Удаляем промпт из ответа
            response = response.replace(prompt, '').strip()
            # Ограничиваем длину ответа до 1000 символов
            if len(response) > 1000:
                response = response[:1000] + "..."
            await update.message.reply_text(response)
        else:
            # Более информативное сообщение об ошибке
            await update.message.reply_text("Извините, не удалось получить ответ от нейросети. Попробуйте позже или отправьте другое сообщение.")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        await update.message.reply_text("Извините, произошла ошибка при обработке вашего сообщения. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        await update.message.reply_text("Извините, произошла ошибка при обработке вашего сообщения. Попробуйте позже.")

# Функция для остановки предыдущего экземпляра бота
async def stop_previous_instance():
    try:
        # Создаем временное приложение
        temp_app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Получаем список активных вебхуков
        webhook_info = await temp_app.bot.get_webhook_info()
        
        # Если есть активный вебхук, удаляем его
        if webhook_info.url:
            await temp_app.bot.delete_webhook()
            logger.info("Удален предыдущий вебхук")
        
        # Очищаем очередь обновлений
        await temp_app.bot.get_updates(timeout=1)
        logger.info("Очищена очередь обновлений")
        
    except Exception as e:
        logger.error(f"Ошибка при остановке предыдущего экземпляра: {str(e)}")

# Основная функция
def main():
    try:
        # Останавливаем предыдущий экземпляр
        import asyncio
        asyncio.run(stop_previous_instance())
        
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("edit", edit_personality))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Бот запущен и готов к работе!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
        raise

if __name__ == '__main__':
    main()