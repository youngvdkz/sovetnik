"""
Обработчики кнопок для Telegram бота.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.inline import InlineKeyboards
from keyboards.reply import ReplyKeyboards
from utils.context import ContextManager
from utils.messages import MessageUtils
from services.gemini import GeminiService
from config import Config

logger = logging.getLogger(__name__)

class ButtonHandlers:
    """Класс обработчиков кнопок"""
    
    def __init__(self, context_manager: ContextManager, gemini_service: GeminiService = None):
        """
        Инициализация обработчиков кнопок
        
        Args:
            context_manager: Менеджер контекста пользователей
            gemini_service: Сервис Gemini для генерации резюме
        """
        self.context_manager = context_manager
        self.gemini_service = gemini_service
        self.inline_keyboards = InlineKeyboards()
        self.reply_keyboards = ReplyKeyboards()
        self.message_utils = MessageUtils()
        logger.info("Инициализированы обработчики кнопок")
    
    async def handle_inline_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик нажатий на inline кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        logger.info(f"Inline кнопка '{data}' от пользователя ID: {user_id}")
        
        if data.startswith("full_"):
            await self._handle_full_answer(query, user_id, data)
        elif data.startswith("short_"):
            await self._handle_short_answer(query, user_id, data)
        elif data.startswith("summary_new_"):
            await self._handle_summary_new_chat(query, user_id, data)
        elif data.startswith("summary_"):
            await self._handle_dialog_summary(query, user_id, data)
        elif data.startswith("new_chat_"):
            await self._handle_new_chat(query, user_id, data)
        elif data.startswith("continue_chat_"):
            await self._handle_continue_chat(query, user_id, data)
        elif data.startswith("context_"):
            await self._handle_context_settings(query, data)
        elif data == "back_main":
            await self._handle_back_main(query)
    
    async def _handle_full_answer(self, query, user_id: int, data: str):
        """Обработка показа полного ответа"""
        parts = data.split("_")
        if len(parts) >= 3:
            answer_user_id = int(parts[1])
            answer_id = int(parts[2])
            
            if answer_user_id == user_id:
                answer_data = self.context_manager.get_full_answer(user_id, answer_id)
                if answer_data:
                    full_text = answer_data['full_answer']
                    
                    # Проверяем, помещается ли полный ответ в одно сообщение
                    if len(full_text) <= Config.MESSAGE_LENGTH_LIMIT:
                        # КОРОТКОЕ СООБЩЕНИЕ: используем старую логику редактирования
                        reply_markup = self.inline_keyboards.get_full_answer_keyboard(user_id, answer_id)
                        
                        await self.message_utils.safe_edit_message(
                            query, full_text, 'Markdown', reply_markup
                        )
                    else:
                        # ДЛИННОЕ СООБЩЕНИЕ: новая логика
                        # 1. Убираем кнопки с краткого ответа (редактируем без кнопок)
                        short_text = answer_data['short_answer']
                        limit_info = self.context_manager.get_limit_info_text(user_id)
                        final_short_text = short_text
                        if limit_info:
                            final_short_text += f"\n\n{limit_info}"
                        
                        # Убираем кнопки с краткого ответа
                        await self.message_utils.safe_edit_message(
                            query, final_short_text, 'Markdown', None
                        )
                        
                        # 2. Отправляем полный ответ частями под кратким
                        reply_markup = self.inline_keyboards.get_answer_keyboard(user_id, answer_id)
                        
                        # Разбиваем на части и отправляем
                        parts = self.message_utils.smart_split_message(full_text)
                        
                        for i, part in enumerate(parts):
                            try:
                                # Добавляем индикатор части для длинных сообщений
                                if len(parts) > 1:
                                    part_indicator = f"\n\n📄 Часть {i+1}/{len(parts)}"
                                    if len(part + part_indicator) <= Config.MESSAGE_LENGTH_LIMIT:
                                        part += part_indicator
                                
                                # Кнопки добавляем только к последней части
                                current_reply_markup = reply_markup if i == len(parts) - 1 else None
                                
                                # Отправляем через query.message с обработкой ошибок Markdown
                                try:
                                    await query.message.reply_text(
                                        part, 
                                        parse_mode='Markdown', 
                                        reply_markup=current_reply_markup
                                    )
                                except Exception as markdown_error:
                                    if "can't parse entities" in str(markdown_error).lower():
                                        # Если ошибка парсинга разметки - отправляем без форматирования
                                        logger.warning(f"Ошибка парсинга Markdown в части {i+1}, отправляю без разметки: {markdown_error}")
                                        await query.message.reply_text(
                                            part, 
                                            reply_markup=current_reply_markup
                                        )
                                    else:
                                        raise markdown_error
                                
                            except Exception as e:
                                logger.error(f"Ошибка отправки части {i+1}/{len(parts)}: {e}")
                                # Отправляем уведомление об ошибке
                                await query.message.reply_text(f"❌ Ошибка отправки части {i+1}. Попробуйте еще раз.")
                else:
                    await self.message_utils.safe_edit_message(query, "❌ Ответ не найден")
    
    async def _handle_short_answer(self, query, user_id: int, data: str):
        """Обработка возврата к краткому ответу"""
        parts = data.split("_")
        if len(parts) >= 3:
            answer_user_id = int(parts[1])
            answer_id = int(parts[2])
            
            if answer_user_id == user_id:
                answer_data = self.context_manager.get_full_answer(user_id, answer_id)
                if answer_data:
                    limit_info = self.context_manager.get_limit_info_text(user_id)
                    short_text = answer_data['short_answer']
                    if limit_info:
                        short_text += f"\n\n{limit_info}"
                    
                    reply_markup = self.inline_keyboards.get_answer_keyboard(user_id, answer_id)
                    
                    await self.message_utils.safe_edit_message(
                        query, short_text, 'Markdown', reply_markup
                    )
    
    async def _handle_dialog_summary(self, query, user_id: int, data: str):
        """Обработка генерации резюме диалога"""
        user_id_from_data = int(data.split("_")[1])
        if user_id_from_data == user_id:
            # Показываем статус
            await self.message_utils.safe_edit_message(
                query, "🦉 Уху..."
            )
            
            # Получаем контекст и генерируем резюме
            context_string = self.context_manager.get_context_string(user_id)
            
            if not context_string.strip():
                await self.message_utils.safe_edit_message(
                    query, "❌ Нет истории диалога для создания резюме."
                )
                return
            
            # Генерируем резюме через Gemini
            if self.gemini_service:
                summary = await self.gemini_service.generate_dialog_summary(context_string)
                
                # Добавляем клавиатуру с полезными действиями
                reply_markup = self.inline_keyboards.get_summary_keyboard(user_id)
                
                # Проверяем длину сообщения и используем подходящий метод отправки
                if len(summary) > Config.MESSAGE_LENGTH_LIMIT:
                    # Для длинных резюме удаляем исходное сообщение и отправляем новые части
                    await query.delete()  # Удаляем исходное сообщение
                    
                    # Разбиваем на части и отправляем через query.message
                    parts = self.message_utils.smart_split_message(summary)
                    
                    for i, part in enumerate(parts):
                        try:
                            # Добавляем индикатор части для длинных сообщений
                            if len(parts) > 1:
                                part_indicator = f"\n\n📄 Часть {i+1}/{len(parts)}"
                                if len(part + part_indicator) <= Config.MESSAGE_LENGTH_LIMIT:
                                    part += part_indicator
                            
                            # Кнопки добавляем только к последней части
                            current_reply_markup = reply_markup if i == len(parts) - 1 else None
                            
                            # Отправляем через query.message с обработкой ошибок Markdown
                            try:
                                await query.message.reply_text(
                                    part, 
                                    parse_mode='Markdown', 
                                    reply_markup=current_reply_markup
                                )
                            except Exception as markdown_error:
                                if "can't parse entities" in str(markdown_error).lower():
                                    logger.warning(f"Ошибка парсинга Markdown в части резюме {i+1}, отправляю без разметки")
                                    await query.message.reply_text(
                                        part, 
                                        reply_markup=current_reply_markup
                                    )
                                else:
                                    raise markdown_error
                        
                        except Exception as e:
                            logger.error(f"Ошибка отправки части резюме {i+1}/{len(parts)}: {e}")
                            await query.message.reply_text(f"❌ Ошибка отправки части {i+1}. Попробуйте еще раз.")
                else:
                    await self.message_utils.safe_edit_message(
                        query, summary, 'Markdown', reply_markup
                    )
            else:
                await self.message_utils.safe_edit_message(
                    query, "❌ Сервис генерации резюме недоступен."
                )
    
    async def _handle_new_chat(self, query, user_id: int, data: str):
        """Обработка начала нового чата"""
        user_id_from_data = int(data.split("_")[2])
        if user_id_from_data == user_id:
            # Очищаем контекст
            self.context_manager.clear_context(user_id)
            
            await self.message_utils.safe_edit_message(
                query, "🆕 **Новый чат начат!**\n\nПамять диалога очищена. Можете задавать новые вопросы."
            )
    
    async def _handle_summary_new_chat(self, query, user_id: int, data: str):
        """Обработка резюме + новый чат"""
        user_id_from_data = int(data.split("_")[2])
        if user_id_from_data == user_id:
            # Показываем статус
            await self.message_utils.safe_edit_message(
                query, "📋🆕 Генерирую резюме и готовлю новый чат..."
            )
            
            # Получаем текущий контекст
            context_string = self.context_manager.get_context_string(user_id)
            
            if not context_string.strip():
                # Если нет контекста, просто начинаем новый чат
                self.context_manager.clear_context(user_id)
                await self.message_utils.safe_edit_message(
                    query, "🆕 **Новый чат начат!**\n\nПредыдущий диалог был пуст."
                )
                return
            
            # Генерируем резюме
            if self.gemini_service:
                summary = await self.gemini_service.generate_dialog_summary(context_string)
                
                # Начинаем новый чат с резюме
                self.context_manager.start_new_chat_with_summary(user_id, summary)
                
                result_text = (
                    f"🔄 Автоматическое обновление чата\n\n"
                    f"Вы достигли лимита в 10 сообщений. Я создал резюме нашего диалога "
                    f"и начал новый чат, сохранив весь контекст!\n\n"
                    f"Резюме предыдущего диалога:\n\n"
                    f"{summary}\n\n"
                    f"---\n\n"
                    f"Теперь можете продолжать общение. Я помню ключевые моменты из предыдущего диалога!"
                )
                
                await self.message_utils.safe_edit_message(
                    query, result_text, 'Markdown'
                )
            else:
                await self.message_utils.safe_edit_message(
                    query, "❌ Сервис генерации резюме недоступен."
                )
    
    async def _handle_continue_chat(self, query, user_id: int, data: str):
        """Обработка продолжения чата"""
        user_id_from_data = int(data.split("_")[2])
        if user_id_from_data == user_id:
            # Просто удаляем сообщение с предупреждением
            await self.message_utils.safe_edit_message(
                query, "✅ **Продолжаем чат!**\n\nУ вас осталось 3 сообщения до автоматического создания резюме."
            )
    
    async def _handle_context_settings(self, query, data: str):
        """Обработка изменения настроек контекста"""
        new_limit = int(data.split("_")[1])
        self.context_manager.update_context_limit(new_limit)
        
        await self.message_utils.safe_edit_message(
            query,
            f"✅ Лимит контекста изменен на {new_limit} сообщений!",
            None,
            self.inline_keyboards.get_settings_keyboard()
        )
    
    async def _handle_back_main(self, query):
        """Обработка возврата в главное меню"""
        await self.message_utils.safe_edit_message(
            query,
            "🏠 Главное меню",
            None,
            self.inline_keyboards.get_main_inline_keyboard()
        )
    
    async def handle_keyboard_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   message_handler, command_handler) -> None:
        """Обработчик обычных кнопок клавиатуры"""
        text = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"Keyboard кнопка '{text}' от пользователя ID: {user_id}")
        
        if text == "❓ Задать вопрос":
            await update.message.reply_text(
                "💬 Напишите ваш вопрос следующим сообщением:",
                reply_markup=self.reply_keyboards.get_main_keyboard()
            )
        elif text == "🎤 Голосовой вопрос":
            await update.message.reply_text(
                "🎙️ Запишите голосовое сообщение с вашим вопросом:",
                reply_markup=self.reply_keyboards.get_main_keyboard()
            )
        elif text == "📊 Статистика":
            await self._handle_statistics(update, user_id)
        elif text == "⚙️ Настройки":
            await self._handle_settings(update)
        elif text == "🧹 Очистить память":
            await self._handle_clear_memory(update, user_id)
        elif text == "ℹ️ Справка":
            await command_handler.help_command(update, context)
        else:
            # Обычное текстовое сообщение - передаем обработчику сообщений
            await message_handler.handle_text_message(update, context)
    
    async def _handle_statistics(self, update: Update, user_id: int):
        """Обработка показа статистики"""
        user_messages = self.context_manager.get_user_message_count(user_id)
        remaining = self.context_manager.get_remaining_messages(user_id)
        
        stats_text = f"Сообщений: {user_messages}/10, осталось: {remaining}"
        await update.message.reply_text(
            stats_text,
            reply_markup=self.reply_keyboards.get_main_keyboard()
        )
    
    async def _handle_settings(self, update: Update):
        """Обработка открытия настроек"""
        await update.message.reply_text(
            "⚙️ **Настройки бота:**\n\nВыберите лимит контекста:",
            parse_mode='Markdown',
            reply_markup=self.inline_keyboards.get_settings_keyboard()
        )
    
    async def _handle_clear_memory(self, update: Update, user_id: int):
        """Обработка очистки памяти"""
        self.context_manager.clear_context(user_id)
        await update.message.reply_text(
            "🧹 Память разговора очищена!",
            reply_markup=self.reply_keyboards.get_main_keyboard()
        ) 