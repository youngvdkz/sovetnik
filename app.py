"""
Flask wrapper для запуска Telegram бота на Render.com
"""

import threading
import time
from flask import Flask, jsonify
from main import main as run_bot
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
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
    """Health check endpoint для Render"""
    return jsonify({
        'status': 'ok',
        'bot_running': bot_status['running'],
        'uptime_seconds': time.time() - bot_status['start_time'] if bot_status['start_time'] else 0,
        'service': 'telegram-bot-adviser'
    })

@app.route('/status')
def status():
    """Детальный статус бота"""
    return jsonify(bot_status)

def run_flask_server():
    """Запуск Flask сервера в отдельном потоке"""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def main():
    """Главная функция - запуск Flask в потоке, Telegram bot в главном потоке"""
    try:
        # Запускаем Flask сервер в отдельном потоке
        flask_thread = threading.Thread(target=run_flask_server, daemon=True)
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
    main() 