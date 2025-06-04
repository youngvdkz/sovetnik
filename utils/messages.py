"""
Утилиты для безопасной работы с сообщениями.
"""

import logging
import re
from typing import Optional, List
from telegram import Update
from telegram.ext import ContextTypes
from config import Config

logger = logging.getLogger(__name__)

class MessageSplitter:
    """Класс для умной разбивки длинных сообщений"""
    
    def __init__(self, max_length: int = Config.MESSAGE_LENGTH_LIMIT):
        self.max_length = max_length
    
    def split(self, text: str) -> List[str]:
        """
        Основной метод разбивки длинного сообщения на части с сохранением Markdown и абзацев
        
        Args:
            text: Текст для разбивки
            
        Returns:
            List[str]: Список частей сообщения
        """
        if len(text) <= self.max_length:
            return [text]
        
        # Разбиваем по абзацам (двойной перенос строки)
        paragraphs = text.split('\n\n')
        parts = []
        current_message = ""
        
        for paragraph in paragraphs:
            test_message = current_message + ('\n\n' if current_message else '') + paragraph
            
            if len(test_message) <= self.max_length and self._is_safe_split_point(test_message):
                # Абзац помещается - добавляем к текущему сообщению
                current_message = test_message
            else:
                # Абзац не помещается - сохраняем текущее сообщение
                if current_message.strip():
                    parts.append(current_message.strip())
                
                # Обрабатываем текущий абзац
                if len(paragraph) <= self.max_length and self._is_safe_split_point(paragraph):
                    current_message = paragraph
                else:
                    # Абзац нужно разбить на части
                    paragraph_parts = self._split_paragraph(paragraph)
                    
                    # Добавляем все части абзаца, кроме последней
                    for part in paragraph_parts[:-1]:
                        if part.strip():
                            parts.append(part.strip())
                    
                    # Последняя часть становится началом нового сообщения
                    current_message = paragraph_parts[-1] if paragraph_parts else ""
        
        # Добавляем последнее сообщение
        if current_message.strip():
            parts.append(current_message.strip())
        
        return self._finalize_parts(parts)
    
    def _count_markdown_tags(self, text: str) -> dict:
        """Подсчитывает открытые/закрытые Markdown теги"""
        counts = {
            '**': text.count('**') % 2,  # bold
            '*': (text.count('*') - text.count('**') * 2) % 2,  # italic  
            '`': text.count('`') % 2,  # code
            '_': text.count('_') % 2,  # underline
        }
        return counts
    
    def _is_safe_split_point(self, text: str) -> bool:
        """Проверяет, безопасно ли разбивать текст в этой точке (все теги закрыты)"""
        counts = self._count_markdown_tags(text)
        all_tags_closed = all(count == 0 for count in counts.values())
        
        # Дополнительная проверка - текст не должен заканчиваться посередине слова
        if text and not text[-1].isspace() and text[-1] not in '.!?,:;':
            if len(text) > 1 and text[-2:].isalnum():
                return False
        
        return all_tags_closed
    
    def _split_paragraph(self, paragraph: str) -> List[str]:
        """Разбивает абзац на части по предложениям"""
        if len(paragraph) <= self.max_length:
            return [paragraph]
        
        parts = []
        current_part = ""
        
        # Разбиваем по предложениям
        sentences = re.split(r'([.!?]+\s)', paragraph)
        
        for sentence in sentences:
            test_part = current_part + sentence
            
            if len(test_part) <= self.max_length and self._is_safe_split_point(test_part):
                current_part = test_part
            else:
                # Сохраняем текущую часть
                if current_part.strip():
                    parts.append(current_part.strip())
                
                # Если предложение слишком длинное, разбиваем по словам
                if len(sentence) > self.max_length:
                    word_parts = self._split_by_words(sentence)
                    parts.extend(word_parts[:-1])
                    current_part = word_parts[-1] if word_parts else ""
                else:
                    current_part = sentence
        
        # Добавляем последнюю часть
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts
    
    def _split_by_words(self, text: str) -> List[str]:
        """Разбивает текст по словам когда предложения слишком длинные"""
        parts = []
        words = text.split(' ')
        current_part = ""
        
        for word in words:
            test_part = current_part + (' ' if current_part else '') + word
            
            if len(test_part) <= self.max_length and self._is_safe_split_point(test_part):
                current_part = test_part
            else:
                if current_part.strip():
                    parts.append(current_part.strip())
                current_part = word
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts
    
    def _finalize_parts(self, parts: List[str]) -> List[str]:
        """Финальная проверка и очистка частей"""
        final_parts = []
        
        for part in parts:
            if part.strip():
                # Проверка безопасности Markdown
                if not self._is_safe_split_point(part):
                    logger.warning(f"Обнаружена потенциальная проблема с Markdown в части длиной {len(part)}, используем fallback")
                    safe_parts = self._safe_fallback_split(part)
                    final_parts.extend(safe_parts)
                else:
                    final_parts.append(part.strip())
        
        return final_parts if final_parts else [text[:self.max_length]]
    
    def _safe_fallback_split(self, text: str) -> List[str]:
        """Безопасное разбиение без сохранения Markdown для проблемных случаев"""
        parts = []
        current_part = ""
        
        # Разбиваем по предложениям без учета Markdown
        sentences = re.split(r'([.!?]+\s+)', text)
        
        for sentence in sentences:
            test_part = current_part + sentence
            
            if len(test_part) <= self.max_length:
                current_part = test_part
            else:
                if current_part.strip():
                    parts.append(current_part.strip())
                
                # Если предложение слишком длинное, разбиваем по словам
                if len(sentence) > self.max_length:
                    words = sentence.split(' ')
                    word_part = ""
                    
                    for word in words:
                        test_word_part = word_part + (' ' if word_part else '') + word
                        
                        if len(test_word_part) <= self.max_length:
                            word_part = test_word_part
                        else:
                            if word_part.strip():
                                parts.append(word_part.strip())
                            word_part = word
                    
                    current_part = word_part
                else:
                    current_part = sentence
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts if parts else [text[:self.max_length]]


class MessageUtils:
    """Утилиты для безопасной отправки сообщений"""
    
    @staticmethod
    def smart_split_message(text: str, max_length: int = Config.MESSAGE_LENGTH_LIMIT) -> List[str]:
        """
        Умная разбивка длинного сообщения на части с сохранением Markdown и абзацев
        """
        splitter = MessageSplitter(max_length)
        return splitter.split(text)

    @staticmethod
    async def send_long_message(update: Update, text: str, parse_mode: str = None, reply_markup=None):
        """
        Отправка длинного сообщения с автоматической разбивкой на части
        """
        parts = MessageUtils.smart_split_message(text)
        
        sent_messages = []
        for i, part in enumerate(parts):
            try:
                # Добавляем индикатор части для длинных сообщений
                if len(parts) > 1:
                    part_indicator = f"\n\n📄 Часть {i+1}/{len(parts)}"
                    # Проверяем, что индикатор помещается
                    if len(part + part_indicator) <= Config.MESSAGE_LENGTH_LIMIT:
                        part += part_indicator
                
                # Кнопки добавляем только к последней части
                current_reply_markup = reply_markup if i == len(parts) - 1 else None
                
                # Пробуем отправить с Markdown
                try:
                    message = await MessageUtils.safe_send_message_with_return(
                        update, part, parse_mode, current_reply_markup
                    )
                    sent_messages.append(message)
                except Exception as markdown_error:
                    if "can't parse entities" in str(markdown_error).lower():
                        logger.warning(f"Ошибка Markdown в части {i+1}, отправляю без разметки")
                        # Отправляем без разметки
                        message = await MessageUtils.safe_send_message_with_return(
                            update, part, None, current_reply_markup
                        )
                        sent_messages.append(message)
                    else:
                        raise markdown_error
                
            except Exception as e:
                logger.error(f"Ошибка отправки части {i+1}/{len(parts)}: {e}")
                # Отправляем уведомление об ошибке
                await MessageUtils.safe_send_message(
                    update, f"❌ Ошибка отправки части {i+1}. Попробуйте еще раз."
                )
        
        return sent_messages

    @staticmethod
    async def safe_send_message(update: Update, text: str, parse_mode: str = None, reply_markup=None):
        """Безопасная отправка сообщения с обработкой ошибок разметки"""
        try:
            # Если сообщение слишком длинное, используем разбивку
            if len(text) > Config.MESSAGE_LENGTH_LIMIT:
                return await MessageUtils.send_long_message(update, text, parse_mode, reply_markup)
            
            await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
        except Exception as e:
            if "can't parse entities" in str(e).lower():
                # Если ошибка парсинга разметки - отправляем без форматирования
                logger.warning(f"Ошибка парсинга Markdown, отправляю без разметки: {e}")
                await update.message.reply_text(text, reply_markup=reply_markup)
            else:
                # Другие ошибки
                logger.error(f"Ошибка отправки сообщения: {e}")
                await update.message.reply_text("❌ Произошла ошибка при отправке ответа. Попробуйте еще раз.")

    @staticmethod
    async def safe_send_message_with_return(update: Update, text: str, parse_mode: str = None, reply_markup=None):
        """Безопасная отправка сообщения с возвратом объекта сообщения"""
        try:
            return await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
        except Exception as e:
            if "can't parse entities" in str(e).lower():
                # Если ошибка парсинга разметки - отправляем без форматирования
                logger.warning(f"Ошибка парсинга Markdown, отправляю без разметки: {e}")
                return await update.message.reply_text(text, reply_markup=reply_markup)
            else:
                # Другие ошибки
                logger.error(f"Ошибка отправки сообщения: {e}")
                return await update.message.reply_text("❌ Произошла ошибка при отправке ответа. Попробуйте еще раз.")

    @staticmethod
    async def safe_edit_message(query, text: str, parse_mode: str = None, reply_markup=None):
        """Безопасное редактирование сообщения с обработкой ошибок разметки"""
        try:
            # Для редактирования все же ограничиваем длину (нельзя редактировать на несколько сообщений)
            if len(text) > Config.MESSAGE_LENGTH_LIMIT:
                text = text[:Config.MESSAGE_CUT_LENGTH] + "\n\n... (сообщение обрезано для редактирования)\n💡 Отправьте новый запрос для полного ответа"
            
            await query.edit_message_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
        except Exception as e:
            error_msg = str(e).lower()
            if "can't parse entities" in error_msg:
                # Если ошибка парсинга разметки - редактируем без форматирования
                logger.warning(f"Ошибка парсинга Markdown при редактировании, убираю разметку: {e}")
                try:
                    if len(text) > Config.MESSAGE_LENGTH_LIMIT:
                        text = text[:Config.MESSAGE_CUT_LENGTH] + "\n\n... (сообщение обрезано для редактирования)\n💡 Отправьте новый запрос для полного ответа"
                    await query.edit_message_text(text, reply_markup=reply_markup)
                except Exception as e2:
                    logger.error(f"Ошибка при повторном редактировании: {e2}")
                    await query.edit_message_text("❌ Ошибка отображения сообщения")
            elif "message is too long" in error_msg or "message_too_long" in error_msg:
                # Сообщение слишком длинное
                short_text = text[:Config.MESSAGE_CUT_LENGTH] + "\n\n... (сообщение обрезано для редактирования)\n💡 Отправьте новый запрос для полного ответа"
                try:
                    await query.edit_message_text(short_text, parse_mode=parse_mode, reply_markup=reply_markup)
                except Exception as e3:
                    logger.error(f"Ошибка при обрезке сообщения: {e3}")
                    await query.edit_message_text("❌ Сообщение слишком длинное. Отправьте новый запрос.")
            else:
                # Другие ошибки
                logger.error(f"Ошибка редактирования сообщения: {e}")
                await query.edit_message_text("❌ Произошла ошибка при редактировании сообщения.")

    @staticmethod
    def safe_fallback_split(text: str, max_len: int) -> List[str]:
        """
        Безопасное разбиение без сохранения Markdown для проблемных случаев
        """
        splitter = MessageSplitter(max_len)
        return splitter._safe_fallback_split(text) 