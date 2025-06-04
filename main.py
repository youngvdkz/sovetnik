"""
Telegram бот-советник с модульной архитектурой.
"""

import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import Config
from utils.context import ContextManager
from services.gemini import GeminiService
from services.speech import SpeechService
from handlers.commands import CommandHandlers
from handlers.messages import MessageHandlers
from handlers.buttons import ButtonHandlers

# Настройка логирования
logging.basicConfig(format=Config.LOG_FORMAT, level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)

class AdvisorBot:
    """Главный класс Telegram бота-советника"""
    
    def __init__(self):
        """Инициализация бота и всех компонентов"""
        logger.info("🚀 Инициализация бота-советника...")
        
        # Проверяем конфигурацию
        Config.validate()
        
        # Инициализируем основные компоненты
        self.context_manager = ContextManager()
        self.gemini_service = GeminiService()
        self.speech_service = SpeechService()
        
        # Инициализируем обработчики
        self.command_handlers = CommandHandlers(self.context_manager)
        self.message_handlers = MessageHandlers(
            self.context_manager, 
            self.gemini_service, 
            self.speech_service
        )
        self.button_handlers = ButtonHandlers(self.context_manager, self.gemini_service)
        
        # Создаем приложение
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Настраиваем обработчики
        self._setup_handlers()
        
        logger.info("✅ Бот-советник успешно инициализирован!")
    
    def _setup_handlers(self):
        """Настройка всех обработчиков событий"""
        logger.info("⚙️ Настраиваю обработчики...")
        
        # Обработчики команд
        self.application.add_handler(CommandHandler("start", self.command_handlers.start))
        self.application.add_handler(CommandHandler("clear", self.command_handlers.clear_command))
        self.application.add_handler(CommandHandler("help", self.command_handlers.help_command))
        
        # Обработчик нажатий на inline кнопки
        self.application.add_handler(CallbackQueryHandler(self.button_handlers.handle_inline_button))
        
        # Обработчик голосовых сообщений
        self.application.add_handler(MessageHandler(filters.VOICE, self.message_handlers.handle_voice_message))
        
        # Обработчик текстовых сообщений (включая кнопки клавиатуры)
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self._handle_text_with_buttons
        ))
        
        logger.info("✅ Обработчики настроены!")
    
    async def _handle_text_with_buttons(self, update, context):
        """Универсальный обработчик текста с поддержкой кнопок"""
        text = update.message.text
        
        # Список кнопок клавиатуры
        keyboard_buttons = [
            "❓ Задать вопрос", "🎤 Голосовой вопрос", "📊 Статистика", 
            "⚙️ Настройки", "🧹 Очистить память", "ℹ️ Справка"
        ]
        
        if text in keyboard_buttons:
            # Обрабатываем как кнопку клавиатуры
            await self.button_handlers.handle_keyboard_button(
                update, context, self.message_handlers, self.command_handlers
            )
        else:
            # Обрабатываем как обычное текстовое сообщение
            await self.message_handlers.handle_text_message(update, context)
    
    def run(self):
        """Запуск бота"""
        logger.info("🔥 Запускаю бота-советника...")
        logger.info(f"📊 Конфигурация:")
        logger.info(f"   🤖 Единая модель Gemini: {Config.GEMINI_MODEL}")
        logger.info(f"   🎧 Режим обработки аудио: {Config.AUDIO_PROCESSING_MODE}")
        logger.info(f"   📝 Режим транскрипции: {Config.TRANSCRIPTION_MODE}")
        logger.info(f"   💬 Лимит контекста: {Config.MAX_CONTEXT_MESSAGES} сообщений")
        logger.info(f"   📄 Лимит сообщения: {Config.MESSAGE_LENGTH_LIMIT} символов")
        logger.info(f"   🎯 Прямая обработка аудио: {'ДА' if Config.should_use_direct_audio_mode() else 'НЕТ'}")
        
        try:
            self.application.run_polling(allowed_updates=['message', 'callback_query'])
        except KeyboardInterrupt:
            logger.info("⛔ Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            raise

def main():
    """Главная функция"""
    try:
        bot = AdvisorBot()
        bot.run()
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        exit(1)

if __name__ == "__main__":
    main() 