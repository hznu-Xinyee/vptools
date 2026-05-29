import httpx
import logging
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)


class ATAService:
    def __init__(self):
        self.base_url = "https://openspeech.bytedance.com/api/v1/vc"
        self.appid = settings.ATA_APPID
        self.access_token = settings.ATA_ACCESS_TOKEN

    async def _retry_with_backoff(self, func, max_retries=5, initial_delay=1.0):
        """
        Retry a function with exponential backoff for 429 errors

        Args:
            func: Async function to retry
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds (will be doubled each retry)
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await func()
            except httpx.HTTPStatusError as e:
                last_exception = e

                # Only retry on 429 (Too Many Requests)
                if e.response.status_code == 429:
                    if attempt < max_retries - 1:
                        delay = initial_delay * (2 ** attempt)
                        logger.warning(
                            f"ATA API 429 错误，第 {attempt + 1}/{max_retries} 次重试，"
                            f"等待 {delay:.1f} 秒后重试..."
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"ATA API 429 错误，已达到最大重试次数 {max_retries}")
                        raise
                else:
                    # For other HTTP errors, don't retry
                    raise
            except Exception as e:
                # For non-HTTP errors, don't retry
                logger.error(f"ATA API 请求失败: {str(e)}")
                raise

        # If we exhausted all retries
        if last_exception:
            raise last_exception
    
    async def submit_audio_binary(self, audio_data: bytes, language: str = "zh-CN"):
        """Submit audio file to ATA using binary upload"""
        async def _submit():
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

        try:
            return await self._retry_with_backoff(_submit)
        except Exception as e:
            logger.error(f"ATA submit error: {str(e)}")
            raise
    
    async def submit_audio(self, audio_url: str, language: str = "zh-CN"):
        """Submit audio file to ATA for subtitle extraction using URL"""
        async def _submit():
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

        try:
            return await self._retry_with_backoff(_submit)
        except Exception as e:
            logger.error(f"ATA submit error: {str(e)}")
            raise
    
    async def get_task_status(self, task_id: str):
        """Query ATA task status"""
        async def _query():
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

        try:
            return await self._retry_with_backoff(_query)
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
