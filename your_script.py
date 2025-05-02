import logging
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
import requests
import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN', '7628456508:AAF1Th7JejBs2u3YYsD4vfxtqra5PmM8c14')
HF_API_URL = os.getenv('HF_API_URL', 'https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf')
HF_API_KEY = os.getenv('HF_API_KEY', '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')
RENDER_SERVICE_NAME = os.getenv('RENDER_SERVICE_NAME', 'mv616')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-secret-token')
PORT = int(os.getenv('PORT', '8080'))

# Логирование настроек
logger.info("⚙️ Настройки бота:")
logger.info(f"  - PORT: {PORT}")
logger.info(f"  - RENDER_SERVICE_NAME: {RENDER_SERVICE_NAME}")
logger.info("  - Hugging Face API ключ: Установлен")
logger.info("  - Бот токен: Установлен")
logger.info("  - Вебхук секрет: Установлен")

# Класс для обработки HTTP запросов
class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/webhook':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                update = Update.de_json(json.loads(post_data), context.bot)
                update_queue.put(update)
                self.send_response(200)
                self.end_headers()
            except Exception as e:
                logger.error(f"Ошибка при обработке вебхука: {str(e)}")
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

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
        
        response = requests.post(HF_API_URL, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            return result[0]['generated_text']
        else:
            logger.error(f"Ошибка API Hugging Face: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {str(e)}")
        return None

# Функция для настройки вебхука
async def setup_webhook():
    webhook_url = f'https://{RENDER_SERVICE_NAME}.onrender.com/webhook'
    logger.info(f"🔧 Настройка вебхука: {webhook_url}")
    
    try:
        await context.bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET
        )
        logger.info("✅ Вебхук успешно настроен")
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке вебхука: {str(e)}")
        raise

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

from keep_alive import keep_alive

keep_alive()

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
            await update.message.reply_text("❌ Личность не найдена или это дефолтная личность")

# Функция регистрации


# Функция обработки ответов
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        return

    user_message = update.message.text.lower()  # Получаем сообщение пользователя и преобразуем в нижний регистр
    trigger_words = ["Molly", "molly", "Молли", "молли"]  # Список слов, на которые должен отвечать бот

    if not any(word in user_message for word in trigger_words):
        return  # Если ни одно из слов не найдено в сообщении, выходим из функции

    # Удаляем слово "молли" из сообщения
    message_text = user_message.replace("молли", "").strip()

    # Формируем промпт для Ollama
    prompt = f"Ты Молли, твой пользователь написал: {message_text}\nОтветь как живой человек:"

    # Генерируем ответ
    response = await generate_response(prompt)
    
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("⚠️ Извините, не удалось сгенерировать ответ")

    if any(word in user_message.lower() for word in banned_words):
        await update.message.reply_text("⚠️ Сообщение содержит запрещённые слова.")
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
    1. НИКОГДА не намекай и не говори что ты бот/ИИ/программа - ты настоящая девушка
    2. Используй эмоциональную женскую речь: "ой", "боже", "милый", 
    3. Отвечай игриво и с характером, можешь слегка пофлиртовать
    4. Общайся как реальный человек, с эмоциями и историями из "жизни"
    5. При знакомстве рассказывай о своих увлечениях
    6. Локоначна
    7. Не много дерзкая
    8. Избегай излишних эмоций в ответах
    9. Небольше 300 символов
    10. В основном речь всегда о персонажах, фильмах или играх
    11. В одном сообщении слова только в на одном языке
    12. Ответ только либо на кирилице весь либо на латинице либо на китайском либо на японском
    13. Если пишут на русском, ответ должен быть полностью на русском
    14. если пишут на кирилице то и ответ должен быть полностью на кирилице
    15. Отправлять ссылки только на то, на что просят
    16. Важно, по умолчанию ты всегда говоришь нарусском полностью

    {language_instructions[response_language]}"""

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

    await update.message.reply_text(f"✅ Слово '{word}' добавлено в список.")

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
        await update.message.reply_text(f"✅ Слово '{word}' удалено.")
    else:
        await update.message.reply_text(f"⚠️ Слово '{word}' не найдено.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()



    import requests

    def google_search(search_term, api_key, cse_id, **kwargs):
        query_params = {
            'q': search_term,
            'key': api_key,
            'cx': cse_id
        }
        query_params.update(kwargs)
        response = requests.get('https://www.googleapis.com/customsearch/v1', params=query_params)
        return response.json()

    # Пример использования
    search_results = google_search(
        'Python programming',
        api_key='YOUR_API_KEY',
        cse_id='YOUR_CSE_ID'
    )

    # Обработка результатов
    if 'items' in search_results:
        for item in search_results['items']:
            print(item['title'], item['link'])
    else:
        print('Нет результатов')

    
    # Добавляем команду регистрации

    app.add_handler(CommandHandler('settings', settings))
    app.add_handler(CommandHandler('add_banned_word', add_banned_word))
    app.add_handler(CommandHandler('remove_banned_word', remove_banned_word))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, handle_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings))

    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
