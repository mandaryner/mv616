import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import openai
import json
import asyncio

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

# История диалога
conversation_history = []

# Функция для инициализации OpenAI
def init_openai():
    try:
        # Настройка OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            logger.error("API ключ OpenAI не найден!")
            return False
        
        # Проверяем подключение
        try:
            openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=1
            )
            logger.info("Успешное подключение к OpenAI")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к OpenAI: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Ошибка инициализации OpenAI: {str(e)}")
        return False

# Функция для получения ответа от OpenAI
def get_openai_response(prompt):
    try:
        # Формируем сообщение для OpenAI
        messages = [
            {"role": "system", "content": f"""
            Ты {PERSONALITY['name']}, {PERSONALITY['age']} лет, {PERSONALITY['occupation']}.
            Твои хобби: {', '.join(PERSONALITY['hobbies'])}
            Твои черты характера: {', '.join(PERSONALITY['personality_traits'])}
            Ты общаешься в стиле: {PERSONALITY['communication_style']}
            Отвечай на русском языке.
            """},
            {"role": "user", "content": prompt}
        ]
        
        # Добавляем историю диалога
        messages.extend(conversation_history[-5:])  # Используем последние 5 сообщений
        
        # Получаем ответ от OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка при получении ответа от OpenAI: {str(e)}")
        return None

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
            "/editname новое_имя\n"
            "/editage новый_возраст\n"
            "/editoccupation новое_занятие\n"
            "/edithobbies новое_хобби1,новое_хобби2\n"
            "/edittraits новая_черта1,новая_черта2\n"
            "/editstyle новый_стиль"
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

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # Отправляем сообщение о том, что обрабатываем запрос
    await update.message.reply_text("Привет! Я обрабатываю ваш запрос. Пожалуйста, подождите немного.")
    
    try:
        # Сохраняем сообщение в историю диалога
        conversation_history.append({"role": "user", "content": user_message})
        
        # Получаем ответ от OpenAI
        response = await get_openai_response(user_message)
        
        if response:
            # Сохраняем ответ в историю диалога
            conversation_history.append({"role": "assistant", "content": response})
            
            # Ограничиваем длину истории диалога
            if len(conversation_history) > 10:
                conversation_history.pop(0)
            
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("Извините, не удалось получить ответ. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        await update.message.reply_text("Извините, произошла ошибка при обработке вашего сообщения. Попробуйте позже.")

# Основная функция
def main():
    try:
        # Инициализируем OpenAI
        if not init_openai():
            logger.error("Не удалось инициализировать OpenAI")
            return
        
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