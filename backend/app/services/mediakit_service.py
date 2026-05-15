import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class MediaKitService:
    def __init__(self):
        self.base_url = "https://mediakit.cn-beijing.volces.com/api/v1"
        self.api_key = settings.VOLCENGINE_API_KEY
    
    async def submit_separate_voice_task(self, video_url: str = None, audio_url: str = None) -> str:
        """Submit audio separation task to MediaKit"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                data = {}
                if video_url:
                    data["video_url"] = video_url
                elif audio_url:
                    data["audio_url"] = audio_url
                else:
                    raise ValueError("Either video_url or audio_url must be provided")
                
                response = await client.post(
                    f"{self.base_url}/tools/separate-voice",
                    json=data,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"MediaKit separate voice response: {result}")
                
                if not result.get("success"):
                    raise Exception(f"MediaKit separate voice failed: {result}")
                
                return result.get("task_id")
        except Exception as e:
            logger.error(f"MediaKit separate voice error: {str(e)}")
            raise
    
    async def get_task_status(self, task_id: str) -> dict:
        """Query MediaKit task status"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/tasks/{task_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"MediaKit query response: {result}")
                return result
        except Exception as e:
            logger.error(f"MediaKit query error: {str(e)}")
            raise
    
    def is_task_completed(self, result: dict) -> bool:
        """Check if MediaKit task is completed"""
        return result.get("status") == "completed"
    
    def is_task_failed(self, result: dict) -> bool:
        """Check if MediaKit task is failed"""
        return result.get("status") == "failed"


mediakit_service = MediaKitService()
