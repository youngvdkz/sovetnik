"""
Пакет сервисов для Telegram бота-советника.
"""

from .gemini import GeminiService
from .speech import SpeechService

__all__ = ['GeminiService', 'SpeechService'] 