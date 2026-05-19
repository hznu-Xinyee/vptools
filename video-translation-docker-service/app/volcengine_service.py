import httpx
from typing import Optional, Dict, Any
from app.config import settings


class VolcEngineService:
    def __init__(self):
        self.api_key = settings.VOLCENGINE_API_KEY
        self.base_url = "https://mediakit.cn-beijing.volces.com/api/v1/tools"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def submit_subtitle_erase_task(
        self,
        video_url: str,
        mode: str = "Subtitle"
    ) -> Dict[str, Any]:
        """Submit a subtitle erase task to VolcEngine"""
        url = f"{self.base_url}/erase-video-subtitle-pro"
        payload = {
            "video_url": video_url,
            "mode": mode
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Query the status of a subtitle erase task"""
        url = f"https://mediakit.cn-beijing.volces.com/api/v1/tasks/{task_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    def is_task_completed(self, task_data: Dict[str, Any]) -> bool:
        """Check if the task is completed"""
        return task_data.get("success", False) and "result" in task_data
    
    def is_task_failed(self, task_data: Dict[str, Any]) -> bool:
        """Check if the task has failed"""
        return not task_data.get("success", False) and "error" in task_data


volcengine_service = VolcEngineService()
