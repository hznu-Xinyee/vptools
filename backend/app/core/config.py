from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/vp_db"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OSS Configuration
    OSS_ACCESS_KEY_ID: str
    OSS_ACCESS_KEY_SECRET: str
    OSS_ENDPOINT: str
    OSS_BUCKET_NAME: str
    OSS_REGION_NAME: Optional[str] = None

    # VolcEngine Configuration
    VOLCENGINE_API_KEY: str

    # ATA Configuration
    ATA_APPID: str
    ATA_ACCESS_TOKEN: str

    # Video Translation Docker Service
    VIDEO_TRANSLATION_DOCKER_URL: Optional[str] = None
    VIDEO_TRANSLATION_DOCKER_URL_TEST: Optional[str] = None

    # FC/Docker Service Callback API Key
    CALLBACK_API_KEY: str = "your-callback-api-key-change-in-production"

    # Aliyun ICE Configuration
    ALIYUN_ICE_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ICE_ACCESS_KEY_SECRET: Optional[str] = None
    ALIYUN_ICE_ENDPOINT: str = "ice.cn-shanghai.aliyuncs.com"
    ALIYUN_ICE_REGION_ID: Optional[str] = None
    ALIYUN_ICE_OUTPUT_PATH: Optional[str] = None


settings = Settings()
