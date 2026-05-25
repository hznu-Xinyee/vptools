import httpx
import logging
from typing import Any, Dict, Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class VideoTranslationService:
    def __init__(self):
        self.service_url = settings.VIDEO_TRANSLATION_DOCKER_URL
        self.service_url_test = settings.VIDEO_TRANSLATION_DOCKER_URL_TEST

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

    async def submit_auto_translation(
        self,
        task_id: int,
        oss_key: str,
        file_url: str,
        original_filename: str,
        target_language: Optional[str] = None,
        target_languages: Optional[List[str]] = None,
        skip_subtitle_erasure: bool = False,
        full_screen_erase: bool = True,
        hide_subtitles: bool = False,
        subtitle_params: Optional[Dict[str, Any]] = None,
        custom_voice_id: Optional[str] = None,
        custom_voice_id_map: Optional[Dict[str, str]] = None,
        continuous_dubbing: bool = False,
        use_test_version: bool = False
    ) -> Dict[str, Any]:
        """Submit auto translation task to docker service"""
        logger.info(f"[自动翻译] submit_auto_translation 接收到 hide_subtitles={hide_subtitles}, use_test_version={use_test_version}")

        # 根据 use_test_version 选择 FC 服务地址
        service_url = self.service_url_test if use_test_version else self.service_url

        if not service_url:
            logger.warning(f"VIDEO_TRANSLATION_DOCKER_URL{'_TEST' if use_test_version else ''} is not configured")
            return {"status": "failed", "error_message": "Docker service URL not configured"}

        logger.info(f"[自动翻译] 使用 FC 服务地址: {service_url}")

        payload = {
            "task_id": task_id,
            "oss_key": oss_key,
            "file_url": file_url,
            "original_filename": original_filename,
            "target_language": target_language,
            "target_languages": target_languages,
            "skip_subtitle_erasure": skip_subtitle_erasure,
            "full_screen_erase": full_screen_erase,
            "hide_subtitles": hide_subtitles,
            "subtitle_params": subtitle_params,
            "custom_voice_id": custom_voice_id,
            "custom_voice_map": custom_voice_id_map,  # 修正字段名
            "continuous_dubbing": continuous_dubbing,
            "use_test_version": use_test_version
        }

        logger.info(
            "Submitting auto translation task_id=%s oss_key=%s target_languages=%s custom_voice_map=%s",
            task_id,
            oss_key,
            target_languages,
            custom_voice_id_map
        )

        async with httpx.AsyncClient(timeout=1800.0) as client:
            response = await client.post(
                f"{service_url.rstrip('/')}/auto-translation",
                json=payload,
                headers={"x-fc-invocation-type": "Async"}
            )
            response.raise_for_status()
            if response.status_code == 202 or not response.content:
                return {
                    "task_id": task_id,
                    "status": "processing",
                    "language_results": {
                        language: {"status": "processing"}
                        for language in (target_languages or ([target_language] if target_language else []))
                    },
                    "message": "FC async invocation accepted"
                }
            return response.json()


video_translation_service = VideoTranslationService()
