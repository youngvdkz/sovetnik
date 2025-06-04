"""
Сервис для распознавания речи.
"""

import logging
import requests
from config import Config

logger = logging.getLogger(__name__)

class SpeechService:
    """Сервис для распознавания речи"""
    
    def __init__(self):
        """Инициализация сервиса речи"""
        self.api_key = Config.GEMINI_API_KEY  # Используем тот же ключ
        logger.info("Инициализирован Speech сервис")
    
    async def transcribe_audio_simple(self, audio_data: bytes) -> str:
        """
        Простая транскрипция через Google Speech API напрямую
        
        Args:
            audio_data: Байты аудиофайла
            
        Returns:
            str: Транскрибированный текст или None при ошибке
        """
        try:
            # Используем Google Speech REST API напрямую
            url = f"https://speech.googleapis.com/v1/speech:recognize?key={self.api_key}"
            
            payload = {
                "config": {
                    "encoding": "OGG_OPUS",
                    "sampleRateHertz": 16000,
                    "languageCode": "ru-RU",
                    "enableAutomaticPunctuation": True
                },
                "audio": {
                    "content": __import__('base64').b64encode(audio_data).decode('utf-8')
                }
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'results' in result and len(result['results']) > 0:
                    transcript = result['results'][0]['alternatives'][0]['transcript']
                    return transcript
                else:
                    return None
            else:
                logger.error(f"Speech API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при транскрипции через Speech API: {e}")
            return None 