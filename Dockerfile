FROM python:3.11-slim

# Устанавливаем зависимости для Ollama
RUN apt-get update && \
    apt-get install -y wget && \
    wget https://ollama.ai/download/ubuntu -O ollama.deb && \
    dpkg -i ollama.deb && \
    rm ollama.deb

# Создаем директорию для приложения
WORKDIR /app

# Копируем файлы приложения
COPY . .

# Устанавливаем Python зависимости
RUN pip install -r requirements.txt

# Запускаем Ollama и загружаем модель
RUN ollama pull mistral

# Запускаем Ollama в фоновом режиме
RUN ollama serve &

# Запускаем бота
CMD ["python", "bot.py"]
