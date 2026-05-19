import io
import uuid
from typing import Optional
import oss2
from app.config import settings


class OSSService:
    def __init__(self):
        self.auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(self.auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)

    def upload_audio(self, audio_data: bytes, content_type: str = "audio/mpeg") -> str:
        key = f"video_translation/audio/{uuid.uuid4().hex}.mp3"
        self.bucket.put_object(key, io.BytesIO(audio_data), headers={"Content-Type": content_type})
        return key

    def upload_file(self, key: str, data, content_type: str = None) -> str:
        if isinstance(data, bytes):
            data = io.BytesIO(data)
        headers = {"Content-Type": content_type} if content_type else {}
        self.bucket.put_object(key, data, headers=headers)
        return key

    def get_file_url(self, key: str) -> str:
        return f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT.replace('https://', '')}/{key}"

    def generate_download_url(self, key: str, expires: int = 604800) -> str:
        return self.bucket.sign_url("GET", key, expires)

    def generate_presigned_url(self, key: str, expires: int = 3600, method: str = 'GET') -> str:
        return self.bucket.sign_url(method, key, expires)


oss_service = OSSService()
