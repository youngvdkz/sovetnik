"""
Flask wrapper для запуска Telegram бота на Render.com
"""

import threading
import time
from flask import Flask, jsonify
from main import main as run_bot
import logging
import os
import asyncio
import aiohttp

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

@app.route('/wake')
def wake_up():
    """Эндпоинт для пробуждения приложения"""
    return "⏰ Bot is awake!"

def run_flask():
    """Запускает Flask сервер в отдельном потоке"""
    port = int(os.environ.get('PORT', 10000))
    logger.info("🌐 Flask сервер запущен в отдельном потоке")
    app.run(host='0.0.0.0', port=port, debug=False)

async def keep_alive():
    """Keep-alive механизм - пингует само себя каждые 10 минут"""
    # Получаем URL приложения из переменной окружения Render
    app_url = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:10000')
    
    while True:
        try:
            await asyncio.sleep(600)  # 10 минут = 600 секунд
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{app_url}/wake") as response:
                    if response.status == 200:
                        logger.info("⏰ Keep-alive ping successful")
                    else:
                        logger.warning(f"⚠️ Keep-alive ping failed: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ Keep-alive error: {e}")
            # Продолжаем работу даже при ошибках пинга

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
    logger.info("🚀 Запускаю приложение с keep-alive механизмом...")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем Telegram бота в главном потоке с keep-alive
    async def run_bot_with_keepalive():
        # Запускаем keep-alive в фоне
        keep_alive_task = asyncio.create_task(keep_alive())
        
        # Запускаем основного бота
        logger.info("🚀 Запускаю Telegram бота в главном потоке...")
        await run_bot()
    
    # Запускаем асинхронно
    asyncio.run(run_bot_with_keepalive()) 