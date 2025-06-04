"""
Тест новой системы лимитов сообщений.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.user import UserData
from utils.context import ContextManager

def test_user_message_counting():
    """Тестируем подсчет сообщений пользователя"""
    print("=== Тест подсчета сообщений пользователя ===")
    
    user = UserData(user_id=1)
    
    # Проверяем начальное состояние
    assert user.get_user_message_count() == 0
    assert user.get_remaining_messages() == 10
    assert not user.should_show_limit_warning()
    assert not user.should_auto_create_summary()
    
    print("✅ Начальное состояние корректно")
    
    # Добавляем сообщения от пользователя и бота
    for i in range(1, 8):
        user.add_to_context("user", f"Вопрос {i}")
        user.add_to_context("assistant", f"Ответ {i}")
        
        print(f"После {i} сообщений: пользователь={user.get_user_message_count()}, осталось={user.get_remaining_messages()}")
        
        if i == 7:
            assert user.should_show_limit_warning()
            print("✅ Предупреждение на 7-м сообщении работает")
        else:
            assert not user.should_show_limit_warning()
    
    # Добавляем еще 3 сообщения до лимита
    for i in range(8, 11):
        user.add_to_context("user", f"Вопрос {i}")
        user.add_to_context("assistant", f"Ответ {i}")
        
        print(f"После {i} сообщений: пользователь={user.get_user_message_count()}, осталось={user.get_remaining_messages()}")
        
        if i >= 10:
            assert user.should_auto_create_summary()
            print("✅ Автоматическое резюме на 10-м сообщении работает")

def test_context_manager():
    """Тестируем менеджер контекста"""
    print("\n=== Тест менеджера контекста ===")
    
    from config import Config
    Config.MAX_CONTEXT_MESSAGES = 20
    
    cm = ContextManager()
    user_id = 123
    
    # Проверяем начальное состояние
    assert cm.get_user_message_count(user_id) == 0
    assert cm.get_remaining_messages(user_id) == 10
    assert not cm.should_show_limit_warning(user_id)
    assert not cm.should_auto_create_summary(user_id)
    
    print("✅ Начальное состояние менеджера корректно")
    
    # Добавляем сообщения
    for i in range(1, 8):
        cm.add_to_context(user_id, "user", f"Вопрос {i}")
        cm.add_to_context(user_id, "assistant", f"Ответ {i}")
        
        if i == 7:
            assert cm.should_show_limit_warning(user_id)
            print("✅ Менеджер: предупреждение на 7-м сообщении работает")
    
    # Тестируем начало нового чата с резюме
    summary = "Тестовое резюме диалога"
    cm.start_new_chat_with_summary(user_id, summary)
    
    assert cm.get_user_message_count(user_id) == 0
    assert cm.get_remaining_messages(user_id) == 10
    assert not cm.should_show_limit_warning(user_id)
    assert not cm.should_auto_create_summary(user_id)
    
    print("✅ Новый чат с резюме работает корректно")

def test_limit_info_text():
    """Тестируем формирование текста лимитов"""
    print("\n=== Тест текста лимитов ===")
    
    cm = ContextManager()
    user_id = 456
    
    # Начальное состояние - информация не показывается
    text = cm.get_limit_info_text(user_id)
    expected = ""
    assert text == expected
    print(f"✅ Начальный текст (пустой): '{text}'")
    
    # После 5 сообщений - информация еще не показывается
    for i in range(5):
        cm.add_to_context(user_id, "user", f"Вопрос {i+1}")
    
    text = cm.get_limit_info_text(user_id)
    expected = ""
    assert text == expected
    print(f"✅ Текст после 5 сообщений (пустой): '{text}'")
    
    # После 7 сообщений - информация еще не показывается
    for i in range(5, 7):
        cm.add_to_context(user_id, "user", f"Вопрос {i+1}")
    
    text = cm.get_limit_info_text(user_id)
    expected = ""
    assert text == expected
    print(f"✅ Текст после 7 сообщений (пустой): '{text}'")
    
    # Проверяем, что предупреждение активируется на 7-м сообщении
    assert cm.should_show_limit_warning(user_id)
    print("✅ Предупреждение активно на 7-м сообщении")
    
    # После 8 сообщений - информация начинает показываться
    cm.add_to_context(user_id, "user", "Вопрос 8")
    
    text = cm.get_limit_info_text(user_id)
    expected = "📊 Ваших сообщений в чате: 8/10 | Осталось: 2"
    assert text == expected
    print(f"✅ Текст после 8 сообщений: {text}")
    
    # После 9 сообщений
    cm.add_to_context(user_id, "user", "Вопрос 9")
    
    text = cm.get_limit_info_text(user_id)
    expected = "📊 Ваших сообщений в чате: 9/10 | Осталось: 1"
    assert text == expected
    print(f"✅ Текст после 9 сообщений: {text}")
    
    # После 10 сообщений
    cm.add_to_context(user_id, "user", "Вопрос 10")
    
    text = cm.get_limit_info_text(user_id)
    expected = "📊 Ваших сообщений в чате: 10/10 | Осталось: 0"
    assert text == expected
    print(f"✅ Текст после 10 сообщений: {text}")

if __name__ == "__main__":
    try:
        test_user_message_counting()
        test_context_manager()
        test_limit_info_text()
        print("\n🎉 Все тесты прошли успешно!")
    except Exception as e:
        print(f"\n❌ Тест провален: {e}")
        import traceback
        traceback.print_exc() 