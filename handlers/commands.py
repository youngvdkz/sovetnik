"""
Обработчики команд для Telegram бота.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.reply import ReplyKeyboards
from utils.context import ContextManager
from config import Config

logger = logging.getLogger(__name__)

class CommandHandlers:
    """Класс обработчиков команд"""
    
    def __init__(self, context_manager: ContextManager):
        """
        Инициализация обработчиков команд
        
        Args:
            context_manager: Менеджер контекста пользователей
        """
        self.context_manager = context_manager
        self.keyboards = ReplyKeyboards()
        logger.info("Инициализированы обработчики команд")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "пользователь"
        
        # Очищаем контекст при начале
        self.context_manager.clear_context(user_id)
        
        welcome_message = (
            f"👋 Привет, {user_name}! Я бот-советник с кнопками для удобства!\n\n"
            "🎯 **Возможности:**\n"
            "• Текстовые и голосовые вопросы\n"
            "• Память разговора\n"
            "• Настраиваемый контекст\n"
            "• Удобные кнопки\n\n"
            "🔽 Используйте кнопки ниже или команды:"
        )
        
        # Отправляем сообщение с основной клавиатурой
        await update.message.reply_text(
            welcome_message,
            reply_markup=self.keyboards.get_main_keyboard(),
            parse_mode='Markdown'
        )
        
        logger.info(f"Команда /start от пользователя {user_name} (ID: {user_id})")
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /clear"""
        user_id = update.effective_user.id
        self.context_manager.clear_context(user_id)
        
        await update.message.reply_text(
            "🧹 Память разговора очищена! Начинаем с чистого листа.",
            reply_markup=self.keyboards.get_main_keyboard()
        )
        
        logger.info(f"Команда /clear от пользователя ID: {user_id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        user_id = update.effective_user.id
        context_limit = self.context_manager.max_context_length
        
        help_text = (
            "ℹ️ **Как пользоваться ботом:**\n\n"
            "1️⃣ Напишите ваш вопрос текстом\n"
            "2️⃣ Или запишите голосовое сообщение\n"
            "3️⃣ Получите краткий ответ\n"
            "4️⃣ При желании раскройте полный ответ\n\n"
            "🧠 **Особенности:**\n"
            "• Я помню наш разговор и отвечаю с учетом контекста\n"
            f"• Максимум {context_limit} последних сообщений в памяти\n"
            "• Каждый пользователь имеет свою историю\n\n"
            "📋 **Команды:**\n"
            "/start - Начать новый разговор\n"
            "/clear - Очистить память разговора\n"
            "/help - Показать эту справку\n\n"
            "🔧 **Примеры:**\n"
            "• Сначала: \"Как найти работу?\"\n"
            "• Потом: \"А что если у меня нет опыта?\"\n"
            "• Я пойму связь между вопросами!\n\n"
            f"💡 **Текущие настройки:**\n"
            f"• Лимит контекста: {context_limit} сообщений\n"
            f"• Модель: {Config.GEMINI_MODEL}"
        )
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=self.keyboards.get_main_keyboard()
        )
        
        logger.info(f"Команда /help от пользователя ID: {user_id}") 