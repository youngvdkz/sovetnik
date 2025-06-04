"""
Reply клавиатуры для Telegram бота.
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton

class ReplyKeyboards:
    """Класс для создания reply клавиатур"""
    
    @staticmethod
    def get_main_keyboard():
        """Создает основную клавиатуру с кнопками"""
        keyboard = [
            [KeyboardButton("❓ Задать вопрос"), KeyboardButton("🎤 Голосовой вопрос")],
            [KeyboardButton("📊 Статистика"), KeyboardButton("⚙️ Настройки")],
            [KeyboardButton("🧹 Очистить память"), KeyboardButton("ℹ️ Справка")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False) 