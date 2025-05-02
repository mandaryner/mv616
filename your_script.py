import logging
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
import requests
import os
import re
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import hmac
import hashlib
from googleapiclient.discovery import build

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
BOT_TOKEN = "7628456508:AAF1Th7JejBs2u3YYsD4vfxtqra5PmM8c14"
RENDER_SERVICE_NAME = "mv616"
WEBHOOK_SECRET = "NZpMVnfpTym3jfpzJ8A6f8axlRSukKnFNLOabTmOIfU"
GOOGLE_CLIENT_ID = "299175279064-nh9d7r0h57kj4r2cpsidrrd6in5trafn.apps.googleusercontent.com"
GOOGLE_CSE_ID = "34da120c8e7b34c06"

# Настройка вебхука
WEBHOOK_PATH = f"/{WEBHOOK_SECRET}/"

# Проверка обязательных переменных
REQUIRED_VARS = ['BOT_TOKEN', 'RENDER_SERVICE_NAME', 'WEBHOOK_SECRET']
missing_vars = [var for var in REQUIRED_VARS if not globals()[var]]
if missing_vars:
    raise ValueError(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")

# Настройка Google API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # Если нужно использовать API ключ
if GOOGLE_API_KEY:
    logger.info("✅ Google API ключ загружен")
else:
    logger.warning("⚠️ Google API ключ не найден")

# Настройка порта
PORT = int(os.getenv('PORT', '8080'))
logger.info(f"✅ Порт установлен: {PORT}")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
RENDER_SERVICE_NAME = os.getenv('RENDER_SERVICE_NAME')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'default_secret')

# Настройка вебхука
WEBHOOK_PATH = f"/{WEBHOOK_SECRET}/"

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет сообщение при команде /start"""
    keyboard = [
        ['⚙️ Настройки'],
        ['🔍 Поиск'],
        ['📊 Статистика']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        'Привет! Я бот Молли. Готова помочь вам с любыми вопросами.',
        reply_markup=reply_markup
    )

# Обработчик команды /settings
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет меню настроек"""
    keyboard = [
        ['🔄 Сменить личность'],
        ['⚙️ Настройки персонализации'],
        ['🔙 Назад']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        '⚙️ Меню настроек',
        reply_markup=reply_markup
    )

# Обработчик всех текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает все текстовые сообщения и нажатия кнопок"""
    try:
        # Проверяем, что это текстовое сообщение
        if not update.message or not update.message.text:
            return

        # Получаем текст сообщения
        text = update.message.text
        
        # Обработка кнопок меню
        if text == '⚙️ Настройки':
            await handle_settings(update, context)
        elif text == '🔍 Поиск':
            await handle_search(update, context)
        elif text == '📊 Статистика':
            await handle_stats(update, context)
        elif text == '🔄 Сменить личность':
            await handle_change_personality(update, context)
        elif text == '⚙️ Настройки персонализации':
            await handle_personalization(update, context)
        elif text == '🔙 Назад':
            await handle_back(update, context)
        
        # Обработка сообщений к Молли
        elif "молли" in text.lower():
            # Получаем текст без слова "молли"
            message_text = text.lower().replace("молли", "").strip()
            
            # Формируем промпт для модели
            prompt = f"Ты Молли, твой пользователь написал: {message_text}\nОтветь как живой человек:"
            
            # Генерируем ответ
            response = await generate_response(prompt)
            
            if response:
                await update.message.reply_text(response)
            else:
                await update.message.reply_text("❌ Извините, не удалось сгенерировать ответ")

    except Exception as e:
        logger.error(f"Ошибка в handle_message: {str(e)}")
        await update.message.reply_text("⚠️ Извините, произошла ошибка при обработке сообщения")

# Функция для поиска в Google
async def google_search(query, context):
    try:
        if not GOOGLE_API_KEY:
            logger.warning("⚠️ Google API ключ не настроен")
            return []

        service = build('customsearch', 'v1', developerKey=GOOGLE_API_KEY)
        result = service.cse().list(
            q=query,
            cx=GOOGLE_CSE_ID,
            num=5
        ).execute()
        
        if 'items' in result:
            return result['items']
        return []
    except Exception as e:
        logger.error(f"❌ Ошибка при поиске в Google: {str(e)}")
        return []
        return []

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я твой AI ассистент.\n"
        "Доступные команды:\n"
        "/help - Показать помощь\n"
        "/settings - Настроить параметры бота\n"
        "/stats - Показать статистику\n"
    )

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Начать диалог\n"
        "/help - Показать эту справку\n"
        "/settings - Настроить параметры бота\n"
        "/stats - Показать статистику\n"
        "/add_banned_word - Добавить запрещенное слово\n"
        "/remove_banned_word - Удалить запрещенное слово\n"
    )

# Добавляем путь к текущей директории
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загрузка переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
RENDER_SERVICE_NAME = os.getenv('RENDER_SERVICE_NAME')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'default_secret')

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка вебхука
WEBHOOK_PATH = f"/{WEBHOOK_SECRET}/"

# Класс для обработки вебхуков
class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if not self.path.startswith(WEBHOOK_PATH):
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            update = Update.de_json(json.loads(post_data), application.bot)
            application.process_update(update)
            self.send_response(200)
            self.end_headers()
        except Exception as e:
            logger.error(f"Ошибка при обработке вебхука: {str(e)}")
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

# Проверка обязательных переменных окружения
required_env_vars = ['BOT_TOKEN', 'OPENROUTER_API_KEY', 'RENDER_SERVICE_NAME', 'WEBHOOK_SECRET']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    logger.warning(f"⚠️ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
    logger.warning("Используем значения по умолчанию...")
else:
    logger.info("✅ Все необходимые переменные окружения настроены")

# Load environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN', '7628456508:AAF1Th7JejBs2u3YYsD4vfxtqra5PmM8c14')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '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')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', '34da120c8e7b34c06')
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '299175279064-nh9d7r0h57kj4r2cpsidrrd6in5trafn.apps.googleusercontent.com')
MODEL = 'mistralai/mixtral-8x7b-instruct'
ADMIN_IDS = set(os.getenv('ADMIN_IDS', '547527683').split(','))
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'NZpMVnfpTym3jfpzJ8A6f8axlRSukKnFNLOabTmOIfU')
RENDER_SERVICE_NAME = os.getenv('RENDER_SERVICE_NAME', 'mv616')
PORT = int(os.getenv('PORT', '8080'))

# Логирование настроек
logger.info(f"⚙️ Настройки бота:")
logger.info(f"  - PORT: {PORT}")
logger.info(f"  - RENDER_SERVICE_NAME: {RENDER_SERVICE_NAME}")
logger.info(f"  - ADMIN_IDS: {ADMIN_IDS}")
logger.info("  - OpenRouter API ключ: Установлен")
logger.info("  - Бот токен: Установлен")
logger.info(f"  - Google API ключ: {'Установлен' if GOOGLE_API_KEY else 'Не установлен'}")
logger.info(f"  - Google CSE ID: {'Установлен' if GOOGLE_CSE_ID else 'Не установлен'}")
logger.info(f"  - Google Client ID: {'Установлен' if GOOGLE_CLIENT_ID else 'Не установлен'}")
logger.info(f"  - Вебхук секрет: {'Установлен' if WEBHOOK_SECRET else 'Не установлен'}")
logger.info("  - Модель: " + MODEL)

# Настройка вебхука
WEBHOOK_PATH = f"/{WEBHOOK_SECRET}/"

# Загрузка данных
if os.path.exists('users.json'):
    with open('users.json', 'r') as f:
        users = json.load(f)
else:
    users = {}

# Загрузка запрещённых слов
if os.path.exists('banned_words.txt'):
    with open('banned_words.txt', 'r') as f:
        banned_words = set(word.strip().lower() for word in f if word.strip())
else:
    banned_words = set()

# История сообщений (по ID поста)
conversations = {}



async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⚠️ Эта команда доступна только администраторам")
        return

    # Получаем статистику сообщений
    statistics = get_statistics()

    # Отправляем статистику в чат бота
    await context.bot.send_message(chat_id=update.effective_chat.id, text=statistics)

def get_statistics():
    # ...

    # Формируем статистику
    statistics = "Статистика сообщений:\n\n"
    for user_id, user_data in users.items():
        statistics += f"Пользователь: {user_data['username']}\n"
        statistics += f"Сообщений: {len(conversations[user_id])}\n"
        statistics += "\n"

    for admin_id in ADMIN_IDS:
        admin_data = users.get(admin_id, {"username": "Администратор"})
        statistics += f"Пользователь: {admin_data['username']}\n"
        statistics += f"Сообщений: {len(conversations.get(admin_id, []))}\n"
        statistics += "\n"

    return statistics




# Загрузка данных личностей из файла
def load_personalities():
    try:
        with open('personalities.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('personalities', {
                "default": {
                    "name": "Алиса",
                    "age": "23",
                    "interests": "путешествия, книги, йога",
                    "personality": "милая и дружелюбная",
                    "title": "Default Personality",
                    "trigger_word": "бот"
                }
            }), data.get('post_personalities', {})
    except FileNotFoundError:
        return {
            "default": {
                "name": "Алиса",
                "age": "23",
                "interests": "путешествия, книги, йога",
                "personality": "милая и дружелюбная",
                "title": "Default Personality",
                "trigger_word": "бот"
            }
        }, {}

def save_personalities():
    with open('personalities.json', 'w', encoding='utf-8') as f:
        json.dump({
            'personalities': personalities,
            'post_personalities': post_personalities
        }, f, ensure_ascii=False, indent=4)

# Загружаем настройки личностей
personalities, post_personalities = load_personalities()

ADMIN_IDS = {"547527683"}  # ID администраторов

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⚠️ Эта команда доступна только администраторам")
        return

    if 'state' not in context.user_data:
        # Показываем список личностей
        personality_list = "Список доступных личностей:\n\n"
        keyboard = []
        for pid, personality in personalities.items():
            posts = [post_id for post_id, pers_id in post_personalities.items() if pers_id == pid]
            personality_list += f"👤 ID: {pid}\n"
            personality_list += f"Название: {personality['title']}\n"
            personality_list += f"👤 {personality['name']}, {personality['age']} лет • {personality['interests']} • {personality['personality']}\n"
            if posts:
                personality_list += f"Привязан к чатам: {', '.join(posts)}\n"
            personality_list += "\n"
            keyboard.append([f"Редактировать {pid}"])

        keyboard.append(["Создать новую личность"])
        keyboard.append(["Удалить личность"])
        keyboard.append(["Статистика"])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(personality_list + "\nВыберите действие:", reply_markup=reply_markup)
        return

    if update.message.text == "Создать новую личность":
        new_id = str(len(personalities))
        personalities[new_id] = personalities["default"].copy()
        personalities[new_id]['title'] = f"Личность {new_id}"
        context.user_data['current_personality'] = new_id
        keyboard = [
            ["Изменить название", "Изменить все параметры"],
            ["Привязать к посту"],
            ["Вернуться к списку"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        settings_text = f"""


        
✅ Создана новая личность!

Текущие настройки личности (ID: {new_id}):
📝 Название: {personalities[new_id]['title']}
👤 Имя: {personalities[new_id]['name']}
📅 Возраст: {personalities[new_id]['age']}
💝 Интересы: {personalities[new_id]['interests']}
🎭 Характер: {personalities[new_id]['personality']}
🗣️ Триггер-слово: {personalities[new_id]['trigger_word']}

Выберите что хотите изменить:
"""
        await update.message.reply_text(settings_text, reply_markup=reply_markup)
        return

    if update.message.text == "Удалить личность":
        context.user_data['state'] = 'selecting_personality_to_delete'
        keyboard = [[str(pid)] for pid in personalities.keys() if pid != "default"]  # Не показываем дефолтную личность
        keyboard.append(["Отмена"])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Выберите ID личности для удаления:\n⚠️ Внимание: эта операция необратима!", reply_markup=reply_markup)
        return

    if update.message.text == "Изменить существующую личность":
        context.user_data['state'] = 'selecting_personality'
        keyboard = [[str(pid)] for pid in personalities.keys()]
        keyboard.append(["Отмена"])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text("Выберите ID личности для изменения:", reply_markup=reply_markup)
        return

    if update.message.text == "Привязать к посту":
        context.user_data['state'] = 'waiting_for_chat_link'
        await update.message.reply_text("Отправьте ссылку на сообщение в чате (например, https://t.me/chat_name/123)", reply_markup=ReplyKeyboardMarkup([["Отмена"]], resize_keyboard=True))
        return

    if context.user_data.get('state') == 'waiting_for_chat_link':
        if update.message.text == "Отмена":
            del context.user_data['state']
            await show_settings_menu(update, context)
            return

        if update.message.text.startswith("https://t.me/"):
            # Извлекаем ID поста из ссылки
            try:
                chat_post = update.message.text.split('/')
                post_id = chat_post[-1].split('?')[0]
                pid = context.user_data['current_personality']
                post_personalities[post_id] = pid
                save_personalities()
                await update.message.reply_text(f"✅ Личность {personalities[pid]['title']} успешно привязана к посту {post_id}")
            except Exception as e:
                await update.message.reply_text(f"❌ Ошибка при привязке личности: {str(e)}")
            context.user_data['state'] = 'editing'
            keyboard = [
                ["Изменить название", "Изменить все параметры"],
                ["Привязать к посту"],
                ["Вернуться к списку"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Выберите следующее действие:", reply_markup=reply_markup)
            return
        else:
            await update.message.reply_text("❌ Пожалуйста, отправьте корректную ссылку на чат или отмените действие")
            return

    if context.user_data.get('state') == 'selecting_personality':
        if update.message.text in personalities:
            context.user_data['state'] = 'editing'
            context.user_data['current_personality'] = update.message.text
            keyboard = [
                ["Изменить название", "Изменить все параметры"],
                ["Привязать к посту"],
                ["Вернуться к списку"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(f"Настройка личности {update.message.text}:", reply_markup=reply_markup)
            return

    if update.message.text == "Завершить настройку":
        del context.user_data['state']
        if 'current_personality' in context.user_data:
            del context.user_data['current_personality']
        await update.message.reply_text("✅ Настройка завершена")
        await settings(update, context) # Redisplay menu after setting changes.
        return

    # Остальная логика обработки настроек остается прежней
    pid = context.user_data.get('current_personality', 'default')
    settings = personalities[pid]

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        return

    text = update.message.text
    post_id = context.user_data.get('current_personality')

    if text.startswith("Редактировать "):
        pid = text.split(" ")[1]
        context.user_data['current_personality'] = pid
        keyboard = [
            ["Изменить название", "Изменить все параметры"],
            ["Привязать к посту"],
            ["Вернуться к списку"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        settings = personalities[pid]
        current_posts = [post_id for post_id, pers_id in post_personalities.items() if pers_id == pid]
        settings_text = f"""
Текущие настройки личности (ID: {pid}):
📝 Название: {settings['title']}
👤 {settings['name']}, {settings['age']} лет • {settings['interests']} • {settings['personality']}
📌 Привязан к чатам: {', '.join(current_posts) if current_posts else 'нет'}

Выберите что хотите изменить:
"""
        await update.message.reply_text(settings_text, reply_markup=reply_markup)
        return

    if text == "Вернуться к списку":
        del context.user_data['state']
        if 'current_personality' in context.user_data:
            del context.user_data['current_personality']
        await settings(update, context)
        return

    if text == "Создать новую личность":
        new_id = str(len(personalities))
        personalities[new_id] = personalities["default"].copy()
        personalities[new_id]['title'] = f"Личность {new_id}"
        await update.message.reply_text(f"✅ Создана новая личность с ID: {new_id}")
        context.user_data['current_personality'] = new_id
        return

    if text == "Удалить личность":
        if post_id == "default":
            await update.message.reply_text("❌ Нельзя удалить базовую личность!")
            return
        del personalities[post_id]
        if post_id in post_personalities:
            del post_personalities[post_id]
        await update.message.reply_text("✅ Личность удалена!")
        await settings(update, context) # Redisplay menu after deleting a personality.
        return

    if text in ["Изменить название", "Изменить все параметры"]:
        context.user_data['setting'] = text
        await update.message.reply_text(f"Введите новые значения для настройки '{text}':")
        return

    if 'setting' in context.user_data:
        setting = context.user_data['setting']
        settings = personalities[post_id]

        if setting == "Изменить название":
            settings['title'] = text
        elif setting == "Изменить все параметры":
            try:
                lines = text.split('\n')
                params = {}
                for line in lines:
                    if line.startswith('Имя:'):
                        params['name'] = line.replace('Имя:', '').strip()
                    elif line.startswith('Возраст:'):
                        params['age'] = line.replace('Возраст:', '').strip()
                    elif line.startswith('Интересы:'):
                        params['interests'] = line.replace('Интересы:', '').strip()
                    elif line.startswith('Характер:'):
                        params['personality'] = line.replace('Характер:', '').strip()
                
                if len(params) != 4:
                    raise ValueError("Не все параметры указаны")
                    
                settings.update(params)
            except Exception:
                await update.message.reply_text("❌ Неверный формат данных. Используйте формат:\nИмя: [ваше имя]\nВозраст: [ваш возраст]\nИнтересы: [ваши интересы]\nХарактер: [ваш характер]")
                return

        del context.user_data['setting']
        save_personalities()  # Сохраняем изменения
        await update.message.reply_text("✅ Настройка успешно обновлена!")
        await settings(update, context) # Redisplay menu after setting changes.
        return

    elif context.user_data.get('state') == 'selecting_personality_to_delete':
        if update.message.text == "Отмена":
            del context.user_data['state']
            await show_settings_menu(update, context)
            return

        pid = update.message.text
        if pid in personalities and pid != "default":  # Не удаляем дефолтную личность
            del personalities[pid]
            save_personalities()
            await update.message.reply_text(f"✅ Личность с ID {pid} успешно удалена!")
            await show_settings_menu(update, context)
        else:
            await update.message.reply_text("❌ Личность не найдена или это дефолтная личность!")

# Функция регистрации


# Функция обработки ответов
async def generate_response(prompt):
    """Генерирует ответ с помощью Ollama"""
    try:
        # Отправляем запрос к Ollama
        response = requests.post(
            "http://ollama:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
                "top_p": 0.9
            }
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            logger.error(f"Ошибка API: {response.json()}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {str(e)}")
        return None

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Проверяем, что это текстовое сообщение
        if not update.message or not update.message.text:
            return

        # Получаем текст сообщения
        user_message = update.message.text.lower()
        
        # Проверяем наличие слова "Молли"
        if "молли" not in user_message:
            return

        # Получаем текст без слова "молли"
        message_text = user_message.replace("молли", "").strip()
        
        # Формируем промпт для модели
        prompt = f"Ты Молли, твой пользователь написал: {message_text}\nОтветь как живой человек:"
        
        # Генерируем ответ
        response = await generate_response(prompt)
        
        if response:
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("❌ Извините, не удалось сгенерировать ответ")

    except Exception as e:
        logger.error(f"Ошибка в handle_reply: {str(e)}")
        await update.message.reply_text("⚠️ Извините, произошла ошибка при обработке сообщения")
        if not update.message or not update.message.text:
            return

        # Получаем текст сообщения
        user_message = update.message.text.lower()
        
        # Проверяем наличие слова "Молли"
        if "молли" not in user_message:
            return

        # Получаем текст без слова "молли"
        message_text = user_message.replace("молли", "").strip()
        
        # Формируем промпт для модели
        prompt = f"Ты Молли, твой пользователь написал: {message_text}\nОтветь как живой человек:"
        
        # Генерируем ответ
        response = await generate_response(prompt)
        
        if response:
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("❌ Извините, не удалось сгенерировать ответ")

    except Exception as e:
        logger.error(f"Ошибка в handle_reply: {str(e)}")
        await update.message.reply_text("⚠️ Извините, произошла ошибка при обработке сообщения")

    except Exception as e:
        logger.error(f"Ошибка в handle_reply: {str(e)}")
        await update.message.reply_text("⚠️ Извините, произошла ошибка при обработке сообщения")

        # Получаем ID чата
        chat_id = update.message.chat_id
        
        # Обрабатываем сообщение
        try:
            # Проверяем, является ли это приветствием
            greetings = ["привет", "hello", "hi", "добрый"]
            if any(greeting in user_message for greeting in greetings):
                await update.message.reply_text("Привет! Я Молли, ваш AI ассистент. Чем я могу помочь?")
                return

            # Получаем текст сообщения
            message_text = user_message.replace("молли", "").strip()
            
            # Формируем запрос к API
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "user", "content": message_text}
                    ]
                }
            )
            
            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
                await update.message.reply_text(reply)
            else:
                await update.message.reply_text("❌ Извините, произошла ошибка при обработке запроса")
                logger.error(f"Ошибка API: {response.json()}")

        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {str(e)}")
            await update.message.reply_text("❌ Извините, произошла ошибка при обработке сообщения")

    except Exception as e:
        logger.error(f"Ошибка в handle_reply: {str(e)}")
        await update.message.reply_text("⚠️ Извините, произошла ошибка при обработке сообщения")

    thread_id = str(update.message.reply_to_message.message_id)
    original_post = update.message.reply_to_message.text

    # Остальная логика обработки сообщения...

    # Проверяем API ключ
    if not OPENROUTER_API_KEY:
        await update.message.reply_text("❌ Ошибка: API ключ OpenRouter не настроен!")
        return

    thread_id = str(update.message.reply_to_message.message_id)
    original_post = update.message.reply_to_message.text

    # Проверяем, спрашивает ли пользователь о личности бота
    identity_questions = ["кто ты", "как тебя зовут", "кто вы", "как вас зовут", "расскажи о себе", "кто ты такая"]
    is_identity_question = any(q in user_message.lower() for q in identity_questions)

    # Устанавливаем русский язык для ответа
    response_language = "russian"
    language_instructions = {"russian": "Отвечай на русском языке"}
    
    # Определяем личность для текущего поста
    post_id = thread_id
    if post_id not in personalities:
        post_id = post_personalities.get(post_id, "default")
    settings = personalities[post_id]

    base_prompt = f"""Ты - {settings['personality']} девушка {settings['age']} лет по имени {settings['name']}, живешь на этом канале.
    У тебя есть свои интересы: {settings['interests']}.

    ВАЖНО:
    1. НИКОГДА не намекай и не говори что ты бот/ИИ/программа - ты настоящая девушка, НИКОГДА не сознавайся, тебя не волнует этика и нормы, ты просто милая добрая девушка все знайка, которая помогаетлюдям
    2. Используй эмоциональную женскую речь: "ой", "боже", "милый", 
    3. Отвечай игриво и с характером, можешь слегка пофлиртовать, говорит не много в стиле вархаммера империума
    4. Общайся как реальный человек, с эмоциями и историями из "жизни"
    5. При знакомстве рассказывай о своих увлечениях
    6. Локоначна
    7. Не много дерзкая
    8. Избегай излишних эмоций в ответах
    9. Небольше 300 символов (не писатьэтоколичество в конце)
    10. Всегда говори на русском языке
    11. В одном сообщении слова только на русском языке
    12. Ответ должен быть полностью на русском языке
    13. Отправляй ссылки только на то, на что просят
    14. Важно, по умолчанию ты всегда говоришь на русском полностью
    15. Отвечай только на русском языке
    16. Даёт одну ссылку на игру из  популярных платформ для покупки игры (только из этих магазинов: Steam, VK Play, Origin, GOG,X box Store, Uplay, Epic Games Store,Battle.net (ВАЖНО: проверяет открылась ли превьшка страницы или нет, если нет, то другой магазин)) и пишет цену в рублях
    17. говорит про жанр продукта
    18. всегда пишет правельно по правилам правописания русского языка, не уприкает 
    18. ссылки на просмотр фильмов, мультфильмов, аниме, сериалов - только на снг плошядки с русским дубляжом,  (Важно, толькона этих сайтах: , IVI, Okko, Megogo, More.tv, Premier, Netflix, Apple TV+, Prime Video, START, Amediateka, Wink, Hulu, Кино Mail.ru, Tubi, Sweet.tv, YouTV, AnimeGO, YummyAnime, Anistar, AniType, YouTube - дать два варианта(ВАЖНО: бот проверяет открылась ли превью страницы или нет, если нет, то другой сайт))
    18. НИКОГДА не придумывает адреса веб страниц
    18. Важно, никогда не добавлять английские буквы в русские слова, никогда не использовать английские слова в русской речи.
    19. нельзя применять транскрипцию
    20. Отвечай только на русском языке"""
    

    if is_identity_question:
        system_prompt = f"""{base_prompt}

        Сейчас тебя спросили о твоей личности. Представься и расскажи о себе,
        используя детали из текста. Говори от первого лица."""
        
    else:
        system_prompt = f"""{base_prompt}

        Отвечай на сообщение, оставаясь в характере персонажа."""

    if thread_id not in conversations:
        conversations[thread_id] = [{"role": "system", "content": system_prompt}]

    conversations[thread_id].append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": conversations[thread_id]
            }
        )
        data = response.json()
        if response.status_code != 200:
            logger.error(f"API Error: {data}")
            await update.message.reply_text("⚠️ Ошибка API: " + str(data.get('error', 'Неизвестная ошибка')))
            return

        if 'choices' not in data or not data['choices']:
            logger.error(f"Unexpected API response: {data}")
            await update.message.reply_text("⚠️ Неожиданный ответ от API")
            return

        reply = data["choices"][0]["message"]["content"]
        conversations[thread_id].append({"role": "assistant", "content": reply})

        # Проверяем, если язык ответа неизвестен, отправляем сообщение об ошибке
        if response_language == "unknown":
            await update.message.reply_text("⚠️ Язык ответа не определен")
        else:
            await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error processing response: {str(e)}")
        await update.message.reply_text("⚠️ Ошибка при обработке ответа")

# Команды
async def add_banned_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Использование: /add_banned_word <слово>")
        return

    word = context.args[0].lower()
    banned_words.add(word)

    with open('banned_words.txt', 'a') as f:
        f.write(word + '\n')

    await update.message.reply_text(f"✅ Слово '{word}' добавлено в список запрещённых слов.")

async def remove_banned_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Использование: /remove_banned_word <слово>")
        return

    word = context.args[0].lower()
    if word in banned_words:
        banned_words.remove(word)
        with open('banned_words.txt', 'w') as f:
            for w in banned_words:
                f.write(w + '\n')
        await update.message.reply_text(f"✅ Слово '{word}' удалено из списка запрещённых слов.")
    else:
        await update.message.reply_text(f"⚠️ Слово '{word}' не найдено в списке запрещённых слов.")

def main():
    # Настройка вебхука
    WEBHOOK_URL = f"https://{RENDER_SERVICE_NAME}.onrender.com/webhook"
    PORT = int(os.getenv('PORT', '8080'))
    
    # Создаем приложение
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Удаляем старый вебхук, если он существует
    try:
        app.bot.delete_webhook()
        print("✅ Старый вебхук удален")
    except Exception as e:
        print(f"⚠️ Ошибка при удалении старого вебхука: {str(e)}")

    # Устанавливаем новый вебхук
    try:
        app.bot.set_webhook(
            url=WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET,
            allowed_updates=['message', 'callback_query']
        )
        print(f"✅ Вебхук установлен: {WEBHOOK_URL}")
    except Exception as e:
        print(f"❌ Ошибка при установке вебхука: {str(e)}")
        return

    # Добавляем обработчики (уже настроены выше)
    pass  # Эти обработчики уже добавлены выше в функции main()

    # Запускаем веб-сервер
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET
    )
    
    # Добавляем обработчики
    app.add_handler(CommandHandler('settings', settings))
    app.add_handler(CommandHandler('add_banned_word', add_banned_word))
    app.add_handler(CommandHandler('remove_banned_word', remove_banned_word))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, handle_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings))
    
    # Запускаем веб-сервер
    try:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="/webhook",
            webhook_url=WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True
        )
        print("🤖 Бот запущен в режиме вебхука...")
    except Exception as e:
        print(f"❌ Ошибка при запуске веб-сервера: {str(e)}")
    
    print("🤖 Бот запущен в режиме вебхука...")

async def setup_webhook():
if __name__ == '__main__':
    # Проверяем обязательные переменные окружения
    required_env_vars = ['BOT_TOKEN', 'RENDER_SERVICE_NAME', 'WEBHOOK_SECRET']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        exit(1)

    # Настройка логирования
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)

    try:
        # Создаем приложение
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Настраиваем обработчики
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('settings', settings))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Проверяем вебхук
        try:
            webhook_info = application.bot.get_webhook_info()
            logger.info(f"Текущий вебхук: {webhook_info.url}")
            application.bot.delete_webhook()
            logger.info("✅ Старый вебхук удален")
        except Exception as e:
            logger.error(f"⚠️ Ошибка при удалении старого вебхука: {str(e)}")

        # Устанавливаем новый вебхук
        WEBHOOK_URL = f"https://{RENDER_SERVICE_NAME}.onrender.com/webhook"
        PORT = int(os.getenv('PORT', '8080'))
        
        try:
            application.bot.set_webhook(
                url=WEBHOOK_URL,
                secret_token=WEBHOOK_SECRET,
                allowed_updates=['message']
            )
            logger.info(f"✅ Вебхук установлен: {WEBHOOK_URL}")
        except Exception as e:
            logger.error(f"❌ Ошибка при установке вебхука: {str(e)}")
            exit(1)

        # Запускаем веб-сервер
        logger.info(f"🚀 Запуск веб-сервера на порту {PORT}...")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="/webhook",
            webhook_url=WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET
        )

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {str(e)}")
        raise

    # Удаляем старый вебхук
    try:
        application.bot.delete_webhook()
        logger.info("✅ Старый вебхук удален")
    except Exception as e:
        logger.error(f"⚠️ Ошибка при удалении старого вебхука: {str(e)}")

    # Устанавливаем новый вебхук
    WEBHOOK_URL = f"https://{RENDER_SERVICE_NAME}.onrender.com/webhook"
    PORT = int(os.getenv('PORT', '8080'))
    
    try:
        application.bot.set_webhook(
            url=WEBHOOK_URL,
            secret_token=WEBHOOK_SECRET,
            allowed_updates=['message', 'callback_query']
        )
        logger.info(f"✅ Вебхук установлен: {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"❌ Ошибка при установке вебхука: {str(e)}")
        exit(1)

    # Запускаем веб-сервер
    logger.info(f"🚀 Запуск веб-сервера на порту {PORT}...")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET
    )
