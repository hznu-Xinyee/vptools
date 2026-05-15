import json
import uuid
import logging
from typing import Any, Dict, Optional
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_ice20201109.client import Client as ICEClient
from alibabacloud_ice20201109 import models as ice_models
from app.config import settings
from app.oss_service import oss_service


logger = logging.getLogger("video_translation_fc.ice")


class ICEService:
    def __init__(self):
        self.enabled = bool(settings.ALIYUN_ICE_ACCESS_KEY_ID and settings.ALIYUN_ICE_ACCESS_KEY_SECRET)
        self.client = None
        if self.enabled:
            config = open_api_models.Config(
                access_key_id=settings.ALIYUN_ICE_ACCESS_KEY_ID,
                access_key_secret=settings.ALIYUN_ICE_ACCESS_KEY_SECRET
            )
            config.endpoint = settings.ALIYUN_ICE_ENDPOINT
            config.region_id = settings.ALIYUN_ICE_REGION_ID
            self.client = ICEClient(config)

    def register_media(self, input_url: str, title: str, media_type: str) -> Optional[str]:
        if not self.client:
            logger.warning("ICE register_media skipped because client is not configured title=%s media_type=%s", title, media_type)
            return None

        logger.info("ICE register_media start title=%s media_type=%s input_url=%s", title, media_type, input_url)
        request = ice_models.RegisterMediaInfoRequest(
            input_url=input_url,
            media_type=media_type,
            title=title
        )
        runtime = util_models.RuntimeOptions(
            autoretry=True,
            max_attempts=3,
            backoff_policy="no",
            backoff_period=1
        )
        response = self.client.register_media_info_with_options(request, runtime)
        logger.info("ICE register_media success title=%s media_id=%s", title, response.body.media_id)
        return response.body.media_id

    async def render(self, timeline_json: Dict[str, Any]) -> Optional[str]:
        if not self.client:
            logger.warning("ICE render skipped because client is not configured")
            return None

        output_key = f"{settings.ALIYUN_ICE_OUTPUT_PATH}/{uuid.uuid4().hex}.mp4"
        output_url = oss_service.get_file_url(output_key)
        signed_output_url = oss_service.generate_download_url(output_key)
        logger.info("ICE render start output_key=%s output_url=%s timeline=%s", output_key, output_url, timeline_json)
        request = ice_models.SubmitMediaProducingJobRequest(
            timeline=json.dumps(timeline_json, ensure_ascii=False),
            output_media_target="oss-object",
            output_media_config=json.dumps({"MediaURL": output_url}, ensure_ascii=False),
            source="OpenAPI"
        )
        response = self.client.submit_media_producing_job(request)
        logger.info("ICE render submitted response=%s signed_output_url=%s", response.body, signed_output_url)
        return signed_output_url


ice_service = ICEService()
