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

        logger.info(f"[ElevenLabs] 初始化服务，API key 存在: {bool(self.api_key)}, ElevenLabs 库已导入: {ElevenLabs is not None}")

        if ElevenLabs and self.api_key:
            self.client = ElevenLabs(api_key=self.api_key)
            logger.info("[ElevenLabs] 客户端初始化成功")
        else:
            if not ElevenLabs:
                logger.warning("[ElevenLabs] ElevenLabs 库未安装")
            if not self.api_key:
                logger.warning("[ElevenLabs] ELEVENLABS_API_KEY 未配置")
    
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
