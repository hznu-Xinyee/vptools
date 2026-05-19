import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class ATAService:
    def __init__(self):
        self.base_url = "https://openspeech.bytedance.com/api/v1/vc"
        self.appid = settings.ATA_APPID
        self.access_token = settings.ATA_ACCESS_TOKEN
    
    async def submit_audio_binary(self, audio_data: bytes, language: str = "zh-CN"):
        """Submit audio file to ATA using binary upload"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/submit",
                    params={
                        "appid": self.appid,
                        "language": language,
                        "use_itn": "True",
                        "use_capitalize": "True",
                        "max_lines": 1,
                        "words_per_line": 15,
                    },
                    content=audio_data,
                    headers={
                        "Content-Type": "audio/mpeg",
                        "Authorization": f"Bearer; {self.access_token}"
                    }
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"ATA submit response: {result}")
                
                if result.get("code") != 0:
                    raise Exception(f"ATA submit failed: {result.get('message')}")
                
                return result.get("id")
        except Exception as e:
            logger.error(f"ATA submit error: {str(e)}")
            raise
    
    async def submit_audio(self, audio_url: str, language: str = "zh-CN"):
        """Submit audio file to ATA for subtitle extraction using URL"""
        try:
            timeout = httpx.Timeout(600.0, connect=60.0, write=600.0, read=600.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/submit",
                    params={
                        "appid": self.appid,
                        "language": language,
                        "use_itn": "True",
                        "use_capitalize": "True",
                        "max_lines": 1,
                        "words_per_line": 15,
                    },
                    json={"url": audio_url},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer; {self.access_token}"
                    }
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"ATA submit response: {result}")
                
                if result.get("code") != 0:
                    raise Exception(f"ATA submit failed: {result.get('message')}")
                
                return result.get("id")
        except Exception as e:
            logger.error(f"ATA submit error: {str(e)}")
            raise
    
    async def get_task_status(self, task_id: str):
        """Query ATA task status"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(
                    f"{self.base_url}/query",
                    params={
                        "appid": self.appid,
                        "id": task_id,
                        "blocking": "0"
                    },
                    headers={
                        "Authorization": f"Bearer; {self.access_token}"
                    }
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"ATA query response: {result}")
                return result
        except Exception as e:
            logger.error(f"ATA query error: {str(e)}")
            raise
    
    def is_task_completed(self, result: dict) -> bool:
        """Check if ATA task is completed"""
        return result.get("code") == 0 and "utterances" in result
    
    def is_task_failed(self, result: dict) -> bool:
        """Check if ATA task is failed"""
        code = result.get("code")
        return code is not None and code != 0 and code != 2000


ata_service = ATAService()
