"""
Обработчики сообщений для Telegram бота.
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from keyboards.inline import InlineKeyboards
from utils.context import ContextManager
from utils.messages import MessageUtils
from services.gemini import GeminiService
from services.speech import SpeechService
from config import Config

logger = logging.getLogger(__name__)

class MessageHandlers:
    """Класс обработчиков сообщений"""
    
    def __init__(self, context_manager: ContextManager, gemini_service: GeminiService, 
                 speech_service: SpeechService):
        """
        Инициализация обработчиков сообщений
        
        Args:
            context_manager: Менеджер контекста пользователей
            gemini_service: Сервис для работы с Gemini
            speech_service: Сервис для распознавания речи
        """
        self.context_manager = context_manager
        self.gemini_service = gemini_service
        self.speech_service = speech_service
        self.inline_keyboards = InlineKeyboards()
        self.message_utils = MessageUtils()
        logger.info("Инициализированы обработчики сообщений")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        
        if not text or text.strip() == "":
            await update.message.reply_text("⚠️ Пустое сообщение. Пожалуйста, задайте вопрос.")
            return
        
        logger.info(f"Текстовое сообщение от пользователя ID: {user_id}, длина: {len(text)}")
        
        # Отправляем сообщение о начале обработки
        thinking_message = await update.message.reply_text("🦉 Уху...")
        
        try:
            # Получаем контекст пользователя
            context_string = self.context_manager.get_context_string(user_id)
            
            # Обрабатываем вопрос через Gemini
            full_answer, short_answer = await self.gemini_service.process_with_context(text, context_string)
            
            # Сохраняем в контекст (это увеличит счетчик пользовательских сообщений)
            self.context_manager.add_to_context(user_id, "user", text)
            self.context_manager.add_to_context(user_id, "assistant", full_answer)
            
            # Создаем ID для ответа и сохраняем полный ответ
            answer_id = self.context_manager.get_next_answer_id(user_id)
            self.context_manager.save_full_answer(user_id, answer_id, full_answer, short_answer, text)
            
            # Формируем краткий ответ для отображения
            limit_info = self.context_manager.get_limit_info_text(user_id)
            response_text = short_answer
            if limit_info:  # Добавляем информацию о лимитах только если она есть
                response_text += f"\n\n{limit_info}"
            
            # Создаем клавиатуру
            reply_markup = self.inline_keyboards.get_answer_keyboard(user_id, answer_id)
            
            # Удаляем сообщение "обрабатываю" и отправляем ответ
            await thinking_message.delete()
            
            await self.message_utils.safe_send_message(
                update, response_text, 'Markdown', reply_markup
            )
            
            # НОВАЯ ЛОГИКА: Проверяем лимиты ПОСЛЕ отправки ответа
            await self._check_and_handle_limits(update, user_id)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке текстового сообщения: {e}")
            await thinking_message.delete()
            await update.message.reply_text("❌ Произошла ошибка при обработке вашего сообщения.")
    
    async def _check_and_handle_limits(self, update: Update, user_id: int):
        """НОВОЕ: Проверяет и обрабатывает лимиты сообщений"""
        
        # Проверяем, нужно ли автоматически создать резюме (10-е сообщение)
        if self.context_manager.should_auto_create_summary(user_id):
            logger.info(f"Пользователь {user_id} достиг лимита 10 сообщений - создаем автоматическое резюме")
            
            # Создаем резюме
            context_string = self.context_manager.get_context_string(user_id)
            summary = await self.gemini_service.generate_dialog_summary(context_string)
            
            # Начинаем новый чат с резюме
            self.context_manager.start_new_chat_with_summary(user_id, summary)
            
            # Отправляем уведомление
            notification_text = (
                "🔄 **Автоматическое обновление чата**\n\n"
                "Вы достигли лимита в 10 сообщений. Я создал резюме нашего диалога "
                "и начал новый чат, сохранив весь контекст!\n\n"
                "Резюме предыдущего диалога:\n\n"
                f"{summary}\n\n"
                "✨ Теперь у вас снова 10 новых сообщений!"
            )
            
            await self.message_utils.safe_send_message(
                update, notification_text, 'Markdown'
            )
            
        # Проверяем, нужно ли показать предупреждение (7-е сообщение)
        elif self.context_manager.should_show_limit_warning(user_id):
            remaining = self.context_manager.get_remaining_messages(user_id)
            logger.info(f"Показываем предупреждение о лимите для пользователя {user_id}, осталось: {remaining}")
            
            warning_text = (
                "⚠️ **Приближение к лимиту сообщений**\n\n"
                f"У вас осталось **{remaining} сообщения** до автоматического создания резюме.\n\n"
                "🤔 **Что вы хотите сделать?**"
            )
            
            reply_markup = self.inline_keyboards.get_limit_warning_keyboard(user_id)
            
            await self.message_utils.safe_send_message(
                update, warning_text, 'Markdown', reply_markup
            )
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик голосовых сообщений с умной логикой транскрипции"""
        user_id = update.effective_user.id
        
        logger.info(f"Голосовое сообщение от пользователя ID: {user_id}")
        
        # Отправляем сообщение о начале обработки
        thinking_message = await update.message.reply_text("🦉 Уху...")
        
        try:
            # Получаем файл
            voice = update.message.voice
            file = await context.bot.get_file(voice.file_id)
            
            # Загружаем аудио данные
            audio_data = await file.download_as_bytearray()
            
            # Проверяем размер файла для выбора стратегии
            file_size_mb = len(audio_data) / (1024 * 1024)
            logger.info(f"Размер аудиофайла: {file_size_mb:.2f} MB, длительность: {voice.duration}s")
            
            # Получаем контекст пользователя
            context_string = self.context_manager.get_context_string(user_id)
            
            # НОВАЯ ЛОГИКА: выбираем режим обработки
            if Config.should_use_direct_audio_mode():
                # ====== РЕЖИМ ПРЯМОЙ ОБРАБОТКИ АУДИО ======
                logger.info(f"Используем прямую обработку аудио через {Config.GEMINI_MODEL}")
                
                # Проверяем лимиты для прямой обработки
                if (file_size_mb > Config.GEMINI_MAX_AUDIO_SIZE_MB or 
                    voice.duration > Config.GEMINI_MAX_AUDIO_DURATION):
                    logger.warning(f"Файл превышает лимиты для прямой обработки - переключаемся на транскрипцию")
                    # Fallback к транскрипции
                    await self._process_with_transcription(
                        update, thinking_message, audio_data, voice, context_string, user_id
                    )
                else:
                    # Прямая обработка аудио
                    await thinking_message.edit_text("🦉 Уху... обрабатываю аудио...")
                    
                    try:
                        full_answer, short_answer = await self.gemini_service.process_audio_with_context(
                            bytes(audio_data), context_string
                        )
                        
                        # Проверяем, что получили валидный ответ
                        if not full_answer or full_answer.strip() == "" or "ошибка" in full_answer.lower():
                            logger.warning("Прямая обработка не дала валидный результат - переключаемся на транскрипцию")
                            await self._process_with_transcription(
                                update, thinking_message, audio_data, voice, context_string, user_id
                            )
                            return
                        
                        # Извлекаем транскрипцию для контекста
                        transcription = await self.gemini_service.extract_transcription_from_response(full_answer)
                        
                        # Сохраняем в контекст
                        self.context_manager.add_to_context(user_id, "user", transcription)
                        self.context_manager.add_to_context(user_id, "assistant", full_answer)
                        
                        # Создаем ID для ответа и сохраняем полный ответ
                        answer_id = self.context_manager.get_next_answer_id(user_id)
                        self.context_manager.save_full_answer(user_id, answer_id, full_answer, short_answer, transcription)
                        
                        # Формируем ответ
                        limit_info = self.context_manager.get_limit_info_text(user_id)
                        response_parts = [short_answer]
                        
                        # Добавляем информацию о лимитах только если она есть
                        if limit_info:
                            response_parts.extend(["", limit_info])
                        
                        response_text = "\n".join(response_parts)
                        
                        # Создаем клавиатуру и отправляем ответ
                        reply_markup = self.inline_keyboards.get_answer_keyboard(user_id, answer_id)
                        await thinking_message.delete()
                        
                        await self.message_utils.safe_send_message(
                            update, response_text, 'Markdown', reply_markup
                        )
                        
                        # НОВАЯ ЛОГИКА: Проверяем лимиты ПОСЛЕ отправки ответа
                        await self._check_and_handle_limits(update, user_id)
                        
                    except Exception as direct_error:
                        logger.error(f"Ошибка прямой обработки аудио: {direct_error}")
                        logger.info("Переключаемся на режим транскрипции как fallback")
                        await self._process_with_transcription(
                            update, thinking_message, audio_data, voice, context_string, user_id
                        )
            
            else:
                # ====== РЕЖИМ ТРАНСКРИПЦИИ ======
                reason = []
                if Config.AUDIO_PROCESSING_MODE != 'direct':
                    reason.append(f"AUDIO_PROCESSING_MODE={Config.AUDIO_PROCESSING_MODE}")
                if not Config.supports_direct_audio_processing():
                    reason.append(f"модель {Config.GEMINI_MODEL} не поддерживает прямую обработку аудио")
                
                reason_str = ", ".join(reason) if reason else "неизвестная причина"
                logger.info(f"Используем режим транскрипции. Причины: {reason_str}")
                await self._process_with_transcription(
                    update, thinking_message, audio_data, voice, context_string, user_id
                )
                
        except Exception as e:
            logger.error(f"Ошибка при обработке голосового сообщения: {e}")
            await thinking_message.delete()
            await update.message.reply_text("❌ Произошла ошибка при обработке голосового сообщения.")
    
    async def _process_with_transcription(self, update, thinking_message, audio_data, voice, context_string, user_id):
        """Вспомогательный метод для обработки через транскрипцию (старый режим)"""
        # Обновляем статус
        try:
            await thinking_message.edit_text("🦉 Уху... транскрибирую...")
        except Exception as edit_error:
            logger.warning(f"Ошибка обновления статуса: {edit_error}")
        
        text = None
        transcription_method = "unknown"
        
        # Умная логика выбора метода транскрипции на основе настроек
        use_gemini = True
        
        # Проверяем режим транскрипции из конфига
        if Config.TRANSCRIPTION_MODE == "speech_api_only":
            use_gemini = False
            logger.info("Режим speech_api_only - используем только Google Speech API")
        elif Config.TRANSCRIPTION_MODE == "gemini_only":
            use_gemini = True
            logger.info("Режим gemini_only - используем только Gemini")
        else:  # auto режим
            # Проверяем ограничения для Gemini
            file_size_mb = len(audio_data) / (1024 * 1024)
            if (file_size_mb > Config.GEMINI_MAX_AUDIO_SIZE_MB or 
                voice.duration > Config.GEMINI_MAX_AUDIO_DURATION):
                use_gemini = False
                logger.info(f"Файл превышает лимиты Gemini (размер: {file_size_mb:.2f}MB, длительность: {voice.duration}s) - используем Speech API")
        
        if not use_gemini:
            # Используем Google Speech API
            try:
                await thinking_message.edit_text("🦉 Уху... использую Google Speech...")
            except Exception as edit_error:
                logger.warning(f"Ошибка обновления статуса: {edit_error}")
            text = await self.speech_service.transcribe_audio_simple(bytes(audio_data))
            transcription_method = "Google Speech API"
        else:
            # Сначала пробуем Gemini (основной метод)
            try:
                try:
                    await thinking_message.edit_text("🦉 Уху... использую Gemini...")
                except Exception as edit_error:
                    logger.warning(f"Ошибка обновления статуса: {edit_error}")
                text = await self.gemini_service.transcribe_audio(bytes(audio_data))
                transcription_method = "Gemini"
                
                if not text and Config.TRANSCRIPTION_MODE != "gemini_only":
                    logger.warning("Gemini вернул пустой результат - переключаемся на Speech API")
                    try:
                        await thinking_message.edit_text("🦉 Уху... переключаюсь на Speech API...")
                    except Exception as edit_error:
                        logger.warning(f"Ошибка обновления статуса: {edit_error}")
                    text = await self.speech_service.transcribe_audio_simple(bytes(audio_data))
                    transcription_method = "Google Speech API (fallback)"
                    
            except Exception as e:
                logger.warning(f"Ошибка в Gemini транскрипции: {e}")
                if Config.TRANSCRIPTION_MODE != "gemini_only":
                    try:
                        await thinking_message.edit_text("🦉 Уху... пробую Speech API...")
                    except Exception as edit_error:
                        logger.warning(f"Ошибка обновления статуса: {edit_error}")
                    text = await self.speech_service.transcribe_audio_simple(bytes(audio_data))
                    transcription_method = "Google Speech API (error fallback)"
                else:
                    text = None
        
        if not text:
            try:
                await thinking_message.edit_text("❌ Не удалось распознать речь. Попробуйте записать сообщение заново или улучшить качество звука.")
            except Exception as edit_error:
                logger.warning(f"Ошибка обновления статуса: {edit_error}")
                await thinking_message.delete()
                await update.message.reply_text("❌ Не удалось распознать речь. Попробуйте записать сообщение заново или улучшить качество звука.")
            return
        
        logger.info(f"Транскрипция завершена ({transcription_method}): {text}")
        
        # Обновляем статус
        try:
            await thinking_message.edit_text("🦉 Уху... генерирую ответ...")
        except Exception as edit_error:
            logger.warning(f"Ошибка обновления статуса: {edit_error}")
        
        # Обрабатываем вопрос
        full_answer, short_answer = await self.gemini_service.process_with_context(text, context_string)
        
        # Сохраняем в контекст
        self.context_manager.add_to_context(user_id, "user", text)
        self.context_manager.add_to_context(user_id, "assistant", full_answer)
        
        # Создаем ID для ответа и сохраняем полный ответ
        answer_id = self.context_manager.get_next_answer_id(user_id)
        self.context_manager.save_full_answer(user_id, answer_id, full_answer, short_answer, text)
        
        # Формируем краткий ответ для отображения
        limit_info = self.context_manager.get_limit_info_text(user_id)
        
        # Формируем текст ответа
        response_parts = [short_answer]
        
        # Добавляем информацию о лимитах только если она есть
        if limit_info:
            response_parts.extend(["", limit_info])
        
        response_text = "\n".join(response_parts)
        
        # Создаем клавиатуру и отправляем ответ
        reply_markup = self.inline_keyboards.get_answer_keyboard(user_id, answer_id)
        await thinking_message.delete()
        
        await self.message_utils.safe_send_message(
            update, response_text, 'Markdown', reply_markup
        )
        
        # НОВАЯ ЛОГИКА: Проверяем лимиты ПОСЛЕ отправки ответа
        await self._check_and_handle_limits(update, user_id) 