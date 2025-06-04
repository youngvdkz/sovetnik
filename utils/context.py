"""
Менеджер контекста пользователей.
"""

from typing import Dict
from collections import defaultdict
from models.user import UserData
from config import Config
import logging

logger = logging.getLogger(__name__)

class ContextManager:
    """Менеджер контекста для всех пользователей"""
    
    def __init__(self):
        self.users: Dict[int, UserData] = {}
        self.max_context_length = Config.MAX_CONTEXT_MESSAGES
    
    def get_user(self, user_id: int) -> UserData:
        """Получает или создает данные пользователя"""
        if user_id not in self.users:
            self.users[user_id] = UserData(
                user_id=user_id,
                max_context_length=self.max_context_length
            )
        return self.users[user_id]
    
    def add_to_context(self, user_id: int, role: str, content: str):
        """Добавляет сообщение в контекст пользователя"""
        user = self.get_user(user_id)
        user.add_to_context(role, content)
    
    def get_context_string(self, user_id: int) -> str:
        """Формирует строку с контекстом разговора"""
        user = self.get_user(user_id)
        return user.get_context_string()
    
    def clear_context(self, user_id: int):
        """Очищает контекст пользователя"""
        if user_id in self.users:
            self.users[user_id].clear_context()
    
    def save_full_answer(self, user_id: int, answer_id: int, full_answer: str, 
                        short_answer: str, question: str, message_id: int = None):
        """Сохраняет полный ответ пользователя"""
        user = self.get_user(user_id)
        user.save_full_answer(answer_id, full_answer, short_answer, question, message_id)
    
    def get_full_answer(self, user_id: int, answer_id: int):
        """Получает полный ответ пользователя"""
        user = self.get_user(user_id)
        return user.get_full_answer(answer_id)
    
    def get_context_count(self, user_id: int) -> int:
        """Возвращает количество сообщений в контексте пользователя (старая логика)"""
        user = self.get_user(user_id)
        return user.get_context_count()
    
    def get_user_message_count(self, user_id: int) -> int:
        """НОВОЕ: Возвращает количество сообщений пользователя"""
        user = self.get_user(user_id)
        return user.get_user_message_count()
    
    def get_remaining_messages(self, user_id: int) -> int:
        """НОВОЕ: Возвращает количество оставшихся сообщений"""
        user = self.get_user(user_id)
        return user.get_remaining_messages()
    
    def should_show_limit_warning(self, user_id: int) -> bool:
        """НОВОЕ: Проверяет, нужно ли показать предупреждение о лимите"""
        user = self.get_user(user_id)
        return user.should_show_limit_warning()
    
    def should_auto_create_summary(self, user_id: int) -> bool:
        """НОВОЕ: Проверяет, нужно ли автоматически создать резюме"""
        user = self.get_user(user_id)
        return user.should_auto_create_summary()
    
    def get_next_answer_id(self, user_id: int) -> int:
        """Возвращает следующий ID для ответа пользователя"""
        user = self.get_user(user_id)
        return user.get_next_answer_id()
    
    def update_context_limit(self, new_limit: int):
        """Обновляет лимит контекста для всех пользователей"""
        self.max_context_length = new_limit
        for user in self.users.values():
            user.max_context_length = new_limit 
    
    def start_new_chat_with_summary(self, user_id: int, summary: str):
        """Начинает новый чат с резюме предыдущего диалога"""
        user = self.get_user(user_id)
        user.start_new_chat_with_summary(summary)
        logger.info(f"Начат новый чат с резюме для пользователя {user_id}")
    
    def get_limit_info_text(self, user_id: int) -> str:
        """НОВОЕ: Формирует текст с информацией о лимитах для пользователя"""
        user_count = self.get_user_message_count(user_id)
        
        # Показываем информацию о лимитах только начиная с 8-го сообщения
        if user_count >= 8:
            remaining = self.get_remaining_messages(user_id)
            return f"📊 Ваших сообщений в чате: {user_count}/10 | Осталось: {remaining}"
        else:
            return ""  # До 8-го сообщения не показываем информацию о лимитах 