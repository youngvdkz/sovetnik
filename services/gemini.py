"""
Сервис для работы с Google Gemini API.
"""

import logging
import google.generativeai as genai
from config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    """Сервис для работы с Gemini API"""
    
    def __init__(self):
        """Инициализация сервиса Gemini"""
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
        # Проверяем возможности модели
        supports_audio = Config.supports_direct_audio_processing()
        
        logger.info(f"🤖 Инициализирован Gemini сервис с единой моделью: {Config.GEMINI_MODEL}")
        logger.info(f"📋 Возможности модели:")
        logger.info(f"   ✅ Обработка текстовых сообщений и промптов")
        logger.info(f"   ✅ Транскрипция аудио")
        logger.info(f"   ✅ Генерация резюме диалогов")
        logger.info(f"   ✅ Сокращение ответов")
        logger.info(f"   {'✅' if supports_audio else '❌'} Прямая обработка аудио")
        
        if supports_audio:
            logger.info(f"🎧 Прямая обработка аудио ВКЛЮЧЕНА - ваши промпты получат доступ к эмоциям и интонации!")
        else:
            logger.info(f"🎧 Прямая обработка аудио недоступна для этой модели")
            logger.info(f"💡 Для включения используйте: gemini-1.5-*, gemini-2.0-* или gemini-2.5-*")
    
    async def process_with_context(self, text: str, context: str) -> tuple[str, str]:
        """
        Обрабатывает текст с помощью Gemini в два этапа с учетом контекста
        
        Args:
            text: Текст пользователя
            context: Контекст разговора
            
        Returns:
            tuple: (полный_ответ, краткий_ответ)
        """
        try:
            # Этап 1: Генерируем развернутый ответ с контекстом
            full_prompt = f"""{Config.MAIN_PROMPT}

{context}Новый вопрос пользователя: {text}

Учитывай весь контекст разговора при формировании ответа. Если вопрос связан с предыдущими, обязательно на это ссылайся."""

            response1 = self.model.generate_content(full_prompt)
            full_answer = response1.text

            # Этап 2: Сокращаем ответ
            summary_prompt = f"{Config.SUMMARY_PROMPT}\n\nТекст для сокращения: {full_answer}"
            response2 = self.model.generate_content(summary_prompt)
            short_answer = response2.text

            return full_answer, short_answer

        except Exception as e:
            logger.error(f"Ошибка при обработке Gemini: {e}")
            error_msg = "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."
            return error_msg, error_msg
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Использует Gemini для транскрипции аудио с улучшенным промптом
        
        Args:
            audio_data: Байты аудиофайла
            
        Returns:
            str: Транскрибированный текст или None при ошибке
        """
        try:
            import tempfile
            import os
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Загружаем аудио в Gemini
            audio_file = genai.upload_file(path=temp_path)
            
            # Ожидаем завершения обработки файла
            import time
            while audio_file.state.name == "PROCESSING":
                time.sleep(2)
                audio_file = genai.get_file(audio_file.name)
            
            if audio_file.state.name == "FAILED":
                logger.error("Ошибка обработки аудиофайла в Gemini")
                return None
            
            # Используем улучшенный промпт для транскрипции
            response = self.model.generate_content([
                Config.AUDIO_TRANSCRIPTION_PROMPT,
                audio_file
            ])
            
            # Удаляем временный файл и файл из Gemini
            os.unlink(temp_path)
            genai.delete_file(audio_file.name)
            
            transcription = response.text.strip()
            
            # Логируем результат
            logger.info(f"Gemini транскрипция завершена, длина: {len(transcription)} символов")
            
            return transcription if transcription else None
            
        except Exception as e:
            logger.error(f"Ошибка при транскрипции через Gemini: {e}")
            return None
    
    async def generate_dialog_summary(self, context: str) -> str:
        """
        Генерирует подробное резюме всего диалога
        
        Args:
            context: Полный контекст диалога
            
        Returns:
            str: Подробное резюме диалога
        """
        try:
            if not context.strip():
                return "Диалог пуст - нет истории для создания резюме."
            
            summary_prompt = f"""{Config.DIALOG_SUMMARY_PROMPT}

{context}

Создай максимально подробное и структурированное резюме этого диалога."""

            response = self.model.generate_content(summary_prompt)
            return response.text

        except Exception as e:
            logger.error(f"Ошибка при генерации резюме диалога: {e}")
            return "Извините, произошла ошибка при создании резюме диалога."

    async def analyze_audio_quality(self, audio_data: bytes) -> dict:
        """
        Анализирует качество аудио перед транскрипцией
        
        Args:
            audio_data: Байты аудиофайла
            
        Returns:
            dict: Информация о качестве аудио
        """
        try:
            import tempfile
            import os
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Загружаем аудио в Gemini
            audio_file = genai.upload_file(path=temp_path)
            
            # Ожидаем завершения обработки файла
            import time
            while audio_file.state.name == "PROCESSING":
                time.sleep(2)
                audio_file = genai.get_file(audio_file.name)
            
            if audio_file.state.name == "FAILED":
                return {"quality": "failed", "readable": False}
            
            # Анализируем качество
            analysis_prompt = """
            Проанализируй качество этого аудиофайла для транскрипции.
            
            Верни ответ в формате:
            Качество: [отличное/хорошее/удовлетворительное/плохое]
            Разборчивость: [да/частично/нет]
            Язык: [русский/английский/другой]
            Длительность: [короткое/среднее/длинное]
            Проблемы: [перечисли если есть]
            """
            
            response = self.model.generate_content([analysis_prompt, audio_file])
            
            # Удаляем файлы
            os.unlink(temp_path)
            genai.delete_file(audio_file.name)
            
            analysis_text = response.text.strip()
            
            # Простой парсинг результата
            quality_info = {
                "quality": "unknown",
                "readable": True,
                "language": "russian",
                "analysis": analysis_text
            }
            
            # Определяем качество из текста
            if "плохое" in analysis_text.lower():
                quality_info["quality"] = "poor"
                quality_info["readable"] = False
            elif "удовлетворительное" in analysis_text.lower():
                quality_info["quality"] = "fair"
            elif "хорошее" in analysis_text.lower():
                quality_info["quality"] = "good"
            elif "отличное" in analysis_text.lower():
                quality_info["quality"] = "excellent"
                
            return quality_info
            
        except Exception as e:
            logger.error(f"Ошибка анализа качества аудио: {e}")
            return {"quality": "unknown", "readable": True, "language": "russian"}

    async def process_audio_with_context(self, audio_data: bytes, context: str) -> tuple[str, str]:
        """
        Обрабатывает аудио напрямую с помощью Gemini 2.5 Pro с учетом контекста
        БЕЗ предварительной транскрипции - более эффективно для сложных промптов
        
        Args:
            audio_data: Байты аудиофайла
            context: Контекст разговора
            
        Returns:
            tuple: (полный_ответ, краткий_ответ)
        """
        try:
            import tempfile
            import os
            
            # Создаем временный файл с правильным расширением
            with tempfile.NamedTemporaryFile(suffix=".oga", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            logger.info(f"Загружаем аудиофайл в Gemini: размер {len(audio_data)} байт")
            
            # Загружаем аудио в Gemini с указанием MIME-типа
            try:
                audio_file = genai.upload_file(
                    path=temp_path,
                    mime_type="audio/ogg"  # Указываем правильный MIME-тип
                )
            except Exception as upload_error:
                logger.warning(f"Ошибка загрузки с MIME audio/ogg: {upload_error}")
                # Пробуем без указания MIME-типа
                audio_file = genai.upload_file(path=temp_path)
            
            # Ожидаем завершения обработки файла
            import time
            max_wait_time = 30  # Максимальное время ожидания
            waited_time = 0
            
            while audio_file.state.name == "PROCESSING" and waited_time < max_wait_time:
                time.sleep(2)
                waited_time += 2
                audio_file = genai.get_file(audio_file.name)
                logger.debug(f"Ожидание обработки аудио: {waited_time}s")
            
            if audio_file.state.name == "FAILED":
                logger.error(f"Ошибка обработки аудиофайла в Gemini: {audio_file.state}")
                error_msg = "Извините, произошла ошибка при обработке аудио. Попробуйте позже."
                return error_msg, error_msg
            
            if audio_file.state.name == "PROCESSING":
                logger.error(f"Таймаут при обработке аудиофайла в Gemini после {max_wait_time}s")
                error_msg = "Извините, обработка аудио заняла слишком много времени. Попробуйте позже."
                return error_msg, error_msg
            
            logger.info(f"Аудиофайл успешно обработан Gemini: {audio_file.state.name}")
            
            # Этап 1: Генерируем развернутый ответ напрямую с аудио
            audio_prompt = f"""{Config.MAIN_PROMPT}

{context}

ВАЖНО: Пользователь отправил голосовое сообщение. 
Анализируй не только содержание, но и тон, эмоции, интонации.
Учитывай весь контекст разговора при формировании ответа.
Если голосовой вопрос связан с предыдущими сообщениями, обязательно на это ссылайся.

Сначала транскрибируй аудио, затем дай развернутый ответ на вопрос пользователя."""

            logger.info("Генерируем ответ с помощью Gemini...")
            response1 = self.model.generate_content([audio_prompt, audio_file])
            
            if not response1.text:
                logger.error("Gemini вернул пустой ответ")
                error_msg = "Извините, не удалось обработать ваше голосовое сообщение."
                return error_msg, error_msg
            
            full_answer = response1.text

            # Этап 2: Сокращаем ответ
            summary_prompt = f"{Config.SUMMARY_PROMPT}\n\nТекст для сокращения: {full_answer}"
            response2 = self.model.generate_content(summary_prompt)
            short_answer = response2.text if response2.text else full_answer

            # Удаляем файлы
            try:
                os.unlink(temp_path)
                genai.delete_file(audio_file.name)
            except Exception as cleanup_error:
                logger.warning(f"Ошибка при очистке файлов: {cleanup_error}")
            
            logger.info(f"Прямая обработка аудио завершена успешно")
            
            return full_answer, short_answer

        except Exception as e:
            logger.error(f"Ошибка при прямой обработке аудио через Gemini: {e}")
            error_msg = "Извините, произошла ошибка при обработке вашего голосового сообщения. Попробуйте позже."
            return error_msg, error_msg

    async def extract_transcription_from_response(self, response_text: str) -> str:
        """
        Извлекает транскрипцию из ответа Gemini для сохранения в контекст
        
        Args:
            response_text: Полный ответ от Gemini
            
        Returns:
            str: Извлеченная транскрипция или упрощенная версия
        """
        try:
            # Пытаемся найти транскрипцию в начале ответа
            lines = response_text.split('\n')
            
            # Ищем строки, которые выглядят как транскрипция
            possible_transcription = []
            
            for line in lines[:10]:  # Проверяем первые 10 строк
                line = line.strip()
                if line and not line.startswith('*') and not line.startswith('#'):
                    # Если строка выглядит как прямая речь или вопрос
                    if ('?' in line or 
                        line.lower().startswith(('как', 'что', 'почему', 'где', 'когда', 'можно', 'дай')) or
                        len(line.split()) > 3):  # Достаточно длинная строка
                        possible_transcription.append(line)
                        
                        # Если нашли достаточно длинную строку, берем её
                        if len(line) > 20:
                            break
            
            if possible_transcription:
                return possible_transcription[0]
            else:
                # Fallback: берем краткое описание
                return "Голосовое сообщение пользователя"
                
        except Exception as e:
            logger.error(f"Ошибка извлечения транскрипции: {e}")
            return "Голосовое сообщение пользователя" 