from typing import Optional
import asyncio
from alibabacloud_ice20201109.client import Client as IceClient
from alibabacloud_ice20201109 import models as ice_models
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from app.core.config import settings


class IceService:
    def __init__(self):
        self.client = None
        if settings.ALIYUN_ICE_ACCESS_KEY_ID and settings.ALIYUN_ICE_ACCESS_KEY_SECRET:
            config = open_api_models.Config(
                access_key_id=settings.ALIYUN_ICE_ACCESS_KEY_ID,
                access_key_secret=settings.ALIYUN_ICE_ACCESS_KEY_SECRET,
                endpoint=settings.ALIYUN_ICE_ENDPOINT
            )
            self.client = IceClient(config)

    def register_media(self, input_url: str, title: str, media_type: str) -> Optional[str]:
        if not self.client:
            return None

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
        return response.body.media_id

    async def submit_music_demix_job(self, input_audio_url: str, output_background_url: str, output_vocal_url: str) -> Optional[str]:
        """Submit MusicDemix job to separate audio into background music and vocals"""
        if not self.client:
            return None

        input_config = ice_models.SubmitIProductionJobRequestInput(
            type="OSS",
            media=input_audio_url
        )

        output_config = ice_models.SubmitIProductionJobRequestOutput(
            type="OSS",
            media=output_background_url
        )

        request = ice_models.SubmitIProductionJobRequest(
            function_name="MusicDemix",
            input=input_config,
            output=output_config
        )

        runtime = util_models.RuntimeOptions(
            autoretry=True,
            max_attempts=3,
            backoff_policy="no",
            backoff_period=1
        )

        try:
            response = self.client.submit_iproduction_job_with_options(request, runtime)
            return response.body.job_id
        except Exception as e:
            print(f"Failed to submit MusicDemix job: {e}")
            return None

    async def get_i_production_job(self, job_id: str) -> Optional[dict]:
        """Query IProduction job status"""
        if not self.client:
            return None

        request = ice_models.QueryIProductionJobRequest(
            job_id=job_id
        )

        runtime = util_models.RuntimeOptions(
            autoretry=True,
            max_attempts=3,
            backoff_policy="no",
            backoff_period=1
        )

        try:
            response = self.client.query_i_production_job_with_options(request, runtime)
            return {
                "status": response.body.status,
                "result": response.body.result
            }
        except Exception as e:
            print(f"Failed to query IProduction job: {e}")
            return None


ice_service = IceService()
