"""
Демонстрация новой логики лимитов сообщений.
"""

from utils.context import ContextManager

def demo_new_limits():
    print('=== Демонстрация новой логики лимитов ===')
    
    cm = ContextManager()
    user_id = 123
    
    for i in range(1, 11):
        cm.add_to_context(user_id, 'user', f'Вопрос {i}')
        limit_info = cm.get_limit_info_text(user_id)
        remaining = cm.get_remaining_messages(user_id)
        warning = cm.should_show_limit_warning(user_id)
        auto_summary = cm.should_auto_create_summary(user_id)
        
        if limit_info:
            print(f'Сообщение {i}: {limit_info}')
        else:
            print(f'Сообщение {i}: (информация скрыта)')
        
        if warning:
            print(f'  -> 🟡 ПРЕДУПРЕЖДЕНИЕ: осталось {remaining} сообщений')
        if auto_summary:
            print(f'  -> 🔴 АВТОСОЗДАНИЕ РЕЗЮМЕ!')

if __name__ == "__main__":
    demo_new_limits() 