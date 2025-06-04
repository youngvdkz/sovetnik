"""
Flask wrapper для запуска Telegram бота на Render.com
"""

import threading
import time
import asyncio
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

def run_telegram_bot():
    """Запуск Telegram бота в отдельном потоке с event loop"""
    try:
        bot_status['running'] = True
        bot_status['start_time'] = time.time()
        bot_status['last_activity'] = time.time()
        
        logger.info("🚀 Запускаю Telegram бота...")
        
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем бота
        run_bot()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в Telegram боте: {e}")
        bot_status['running'] = False
    finally:
        bot_status['running'] = False

if __name__ == '__main__':
    # Запускаем Telegram бота в отдельном потоке
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер для health checks
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False) 