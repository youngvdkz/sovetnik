"""
Inline клавиатуры для Telegram бота.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class InlineKeyboards:
    """Класс для создания inline клавиатур"""
    
    @staticmethod
    def get_answer_keyboard(user_id: int, answer_id: int):
        """Создает клавиатуру для краткого ответа"""
        keyboard = [
            [
                InlineKeyboardButton("📝 Полный ответ", callback_data=f"full_{user_id}_{answer_id}")
            ],
            [
                InlineKeyboardButton("📋 Резюме диалога", callback_data=f"summary_{user_id}"),
                InlineKeyboardButton("🆕 Новый чат", callback_data=f"new_chat_{user_id}")
            ],
            [
                InlineKeyboardButton("📋➕🆕 Резюме + новый чат", callback_data=f"summary_new_{user_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_full_answer_keyboard(user_id: int, answer_id: int):
        """Создает клавиатуру для полного ответа"""
        keyboard = [
            [
                InlineKeyboardButton("💡 Свернуть", callback_data=f"short_{user_id}_{answer_id}")
            ],
            [
                InlineKeyboardButton("📋 Резюме диалога", callback_data=f"summary_{user_id}"),
                InlineKeyboardButton("🆕 Новый чат", callback_data=f"new_chat_{user_id}")
            ],
            [
                InlineKeyboardButton("📋➕🆕 Резюме + новый чат", callback_data=f"summary_new_{user_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_settings_keyboard():
        """Создает клавиатуру настроек"""
        keyboard = [
            [
                InlineKeyboardButton("📏 Лимит контекста: 10", callback_data="context_10"),
                InlineKeyboardButton("📏 Лимит контекста: 20", callback_data="context_20")
            ],
            [
                InlineKeyboardButton("📏 Лимит контекста: 50", callback_data="context_50"),
                InlineKeyboardButton("📏 Лимит контекста: 100", callback_data="context_100")
            ],
            [
                InlineKeyboardButton("🔙 Назад", callback_data="back_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_main_inline_keyboard():
        """Создает основную inline клавиатуру"""
        keyboard = [
            [
                InlineKeyboardButton("📝 Полный ответ", callback_data="detailed")
            ],
            [
                InlineKeyboardButton("📋 Резюме диалога", callback_data="summary"),
                InlineKeyboardButton("🆕 Новый чат", callback_data="new_chat")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_summary_keyboard(user_id: int):
        """Создает клавиатуру для резюме диалога"""
        keyboard = [
            [
                InlineKeyboardButton("🆕 Новый чат", callback_data=f"new_chat_{user_id}"),
                InlineKeyboardButton("📋➕🆕 Резюме + новый чат", callback_data=f"summary_new_{user_id}")
            ],
            [
                InlineKeyboardButton("🧹 Очистить память", callback_data=f"clear_memory_{user_id}"),
                InlineKeyboardButton("📊 Статистика", callback_data=f"statistics_{user_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_limit_warning_keyboard(user_id: int):
        """НОВОЕ: Создает клавиатуру для предупреждения о лимите (7-е сообщение)"""
        keyboard = [
            [
                InlineKeyboardButton("📋 Создать резюме", callback_data=f"summary_{user_id}"),
                InlineKeyboardButton("📋➕🆕 Резюме + новый чат", callback_data=f"summary_new_{user_id}")
            ],
            [
                InlineKeyboardButton("✅ Продолжить (осталось 3)", callback_data=f"continue_chat_{user_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard) 