import httpx
import logging
from typing import Any, Dict, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class VideoTranslationService:
    def __init__(self):
        self.service_url = settings.VIDEO_TRANSLATION_DOCKER_URL

    async def submit_task(
        self,
        media_id: str,
        subtitle_json: Any,
        target_language: str,
        task_id: int,
        subtitle_params: Optional[Dict[str, Any]] = None,
        background_audio_media_id: Optional[str] = None,
        background_audio_url: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        if not self.service_url:
            logger.warning("VIDEO_TRANSLATION_DOCKER_URL is not configured")
            return {"docker_task_id": None, "status": "processing"}

        payload = {
            "task_id": task_id,
            "media_id": media_id,
            "subtitle_json": subtitle_json,
            "target_language": target_language
        }

        if subtitle_params:
            normalized_subtitle_params = dict(subtitle_params)
            if "font" in normalized_subtitle_params and "Font" not in normalized_subtitle_params:
                normalized_subtitle_params["Font"] = normalized_subtitle_params["font"]
            payload["subtitle_params"] = normalized_subtitle_params

        if background_audio_media_id:
            payload["background_audio_media_id"] = background_audio_media_id
        if background_audio_url:
            payload["background_audio_url"] = background_audio_url

        logger.info(
            "Submitting video translation task_id=%s media_id=%s background_audio_media_id=%s background_audio_url_present=%s",
            task_id,
            media_id,
            background_audio_media_id,
            bool(background_audio_url)
        )

        async with httpx.AsyncClient(timeout=1800.0) as client:
            response = await client.post(
                f"{self.service_url.rstrip('/')}/translate-video",
                json=payload
            )
            response.raise_for_status()
            return response.json()


video_translation_service = VideoTranslationService()
