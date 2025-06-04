"""
Модели пользовательских данных.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class UserData:
    """Данные пользователя"""
    user_id: int
    context_messages: List[Dict[str, str]] = field(default_factory=list)
    full_answers: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    user_message_count: int = 0  # НОВОЕ: счетчик сообщений только от пользователя
    max_context_length: int = 20  # Для хранения истории (старая логика)
    
    def add_to_context(self, role: str, content: str):
        """Добавляет сообщение в контекст пользователя"""
        self.context_messages.append({
            'role': role,
            'content': content
        })
        
        # НОВОЕ: увеличиваем счетчик только для сообщений пользователя
        if role == 'user':
            self.user_message_count += 1
        
        # Ограничиваем размер контекста для хранения истории
        if len(self.context_messages) > self.max_context_length:
            self.context_messages = self.context_messages[-self.max_context_length:]
    
    def get_context_string(self) -> str:
        """Формирует строку с контекстом разговора"""
        if not self.context_messages:
            return ""
        
        context_parts = []
        for msg in self.context_messages:
            if msg['role'] == 'user':
                context_parts.append(f"Пользователь: {msg['content']}")
            else:
                context_parts.append(f"Советник: {msg['content']}")
        
        return "История разговора:\n" + "\n".join(context_parts) + "\n\n"
    
    def clear_context(self):
        """Очищает контекст пользователя и сбрасывает счетчик"""
        self.context_messages.clear()
        self.full_answers.clear()
        self.user_message_count = 0  # НОВОЕ: сброс счетчика
    
    def start_new_chat_with_summary(self, summary: str):
        """Начинает новый чат с резюме предыдущего диалога"""
        # Очищаем контекст и счетчик
        self.context_messages.clear()
        self.full_answers.clear()
        self.user_message_count = 0
        
        # Добавляем резюме как первое сообщение "системы" (не увеличивает счетчик)
        self.context_messages.append({
            'role': 'assistant',
            'content': f"Резюме предыдущего диалога: {summary}"
        })
    
    def save_full_answer(self, answer_id: int, full_answer: str, short_answer: str, 
                        question: str, message_id: Optional[int] = None):
        """Сохраняет полный ответ для возможности показа по запросу"""
        self.full_answers[answer_id] = {
            'full_answer': full_answer,
            'short_answer': short_answer,
            'question': question,
            'message_id': message_id
        }
    
    def get_full_answer(self, answer_id: int) -> Optional[Dict[str, Any]]:
        """Получает полный ответ по ID"""
        return self.full_answers.get(answer_id)
    
    def get_context_count(self) -> int:
        """Возвращает количество сообщений в контексте (старая логика)"""
        return len(self.context_messages)
    
    def get_user_message_count(self) -> int:
        """НОВОЕ: Возвращает количество сообщений пользователя в текущем чате"""
        return self.user_message_count
    
    def get_remaining_messages(self) -> int:
        """НОВОЕ: Возвращает количество оставшихся сообщений до лимита (10)"""
        return max(0, 10 - self.user_message_count)
    
    def should_show_limit_warning(self) -> bool:
        """НОВОЕ: Проверяет, нужно ли показать предупреждение (на 7-м сообщении)"""
        return self.user_message_count == 7
    
    def should_auto_create_summary(self) -> bool:
        """НОВОЕ: Проверяет, нужно ли автоматически создать резюме (на 10-м сообщении)"""
        return self.user_message_count >= 10
    
    def get_next_answer_id(self) -> int:
        """Возвращает следующий ID для ответа"""
        return len(self.full_answers) 