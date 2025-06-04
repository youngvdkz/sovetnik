"""
Flask wrapper для запуска Telegram бота на Koyeb.
"""

import threading
import time
from flask import Flask, jsonify
from main import main as run_bot
import logging
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

# Флаг состояния бота
bot_status = {
    'running': False,
    'start_time': None,
    'last_activity': None
}

@app.route('/')
def health_check():
    """Health check endpoint для Koyeb"""
    return jsonify({
        'status': 'ok',
        'bot_running': bot_status['running'],
        'uptime_seconds': time.time() - bot_status['start_time'] if bot_status['start_time'] else 0,
        'service': 'telegram-bot-adviser',
        'platform': 'koyeb'
    })

@app.route('/status')
def status():
    """Детальный статус бота"""
    return jsonify(bot_status)

def run_flask():
    """Запускает Flask сервер в отдельном потоке"""
    port = int(os.environ.get('PORT', 8000))  # Koyeb использует порт 8000 по умолчанию
    logger.info("🌐 Flask сервер запущен в отдельном потоке")
    app.run(host='0.0.0.0', port=port, debug=False)

def main():
    """Главная функция - запуск Flask в потоке, Telegram bot в главном потоке"""
    try:
        # Запускаем Flask сервер в отдельном потоке
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        logger.info("🌐 Flask сервер запущен в отдельном потоке")
        time.sleep(2)  # Даем Flask время запуститься
        
        # Обновляем статус
        bot_status['running'] = True
        bot_status['start_time'] = time.time()
        bot_status['last_activity'] = time.time()
        
        logger.info("🚀 Запускаю Telegram бота в главном потоке...")
        
        # Запускаем Telegram бота в главном потоке
        run_bot()
        
    except KeyboardInterrupt:
        logger.info("⛔ Сервис остановлен пользователем")
        bot_status['running'] = False
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        bot_status['running'] = False
        raise

if __name__ == '__main__':
    logger.info("🚀 Запускаю приложение на Koyeb...")
    main() 