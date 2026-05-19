import asyncio
import logging
import os
from typing import Optional

try:
    from elevenlabs.client import ElevenLabs
except ImportError:
    ElevenLabs = None

from app.config import settings

logger = logging.getLogger(__name__)


class ElevenLabsService:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.model_id = "eleven_flash_v2_5"
        self.client = None
        
        if ElevenLabs and self.api_key:
            self.client = ElevenLabs(api_key=self.api_key)
    
    async def synthesize(self, text: str, voice_id: str) -> bytes:
        """Synthesize speech using ElevenLabs"""
        if not self.client:
            raise RuntimeError("ElevenLabs client not configured")
        
        try:
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=self.model_id,
                output_format="mp3_44100_128",
            )
            
            audio_data = b""
            for chunk in audio_generator:
                audio_data += chunk
            
            return audio_data
        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {str(e)}")
            raise RuntimeError(f"ElevenLabs TTS failed: {str(e)}")


elevenlabs_service = ElevenLabsService()
