from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OSS_ACCESS_KEY_ID: str
    OSS_ACCESS_KEY_SECRET: str
    OSS_ENDPOINT: str
    OSS_BUCKET_NAME: str
    OSS_REGION_NAME: Optional[str] = None

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_BASE_URL: str = "https://api.kie.ai"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ARK (Doubao) Configuration for translation
    ARK_API_KEY: Optional[str] = None
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    ARK_MODEL: str = "ep-20241230110113-lnfxh"

    ALIYUN_NLS_URL: str = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
    ALIYUN_NLS_APPKEY: Optional[str] = None
    ALIYUN_NLS_TOKEN: Optional[str] = None
    ALIYUN_NLS_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_NLS_ACCESS_KEY_SECRET: Optional[str] = None
    ALIYUN_NLS_TOKEN_REGION_ID: str = "cn-shanghai"
    ALIYUN_NLS_TOKEN_DOMAIN: str = "nls-meta.cn-shanghai.aliyuncs.com"
    ALIYUN_NLS_TOKEN_REFRESH_MARGIN_SECONDS: int = 600
    ALIYUN_NLS_FORMAT: str = "mp3"
    ALIYUN_NLS_SAMPLE_RATE: int = 16000
    ALIYUN_NLS_VOLUME: int = 50
    ALIYUN_NLS_SPEECH_RATE: int = 166
    ALIYUN_NLS_PITCH_RATE: int = 0
    ALIYUN_NLS_ENABLE_SUBTITLE: bool = False
    ALIYUN_NLS_TIMEOUT_SECONDS: float = 60.0
    ALIYUN_NLS_MAX_TEXT_LENGTH: int = 300
    ALIYUN_NLS_VOICE_MAP_JSON: Optional[str] = None

    ALIYUN_ICE_ENDPOINT: str = "ice.cn-shanghai.aliyuncs.com"
    ALIYUN_ICE_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ICE_ACCESS_KEY_SECRET: Optional[str] = None
    ALIYUN_ICE_REGION_ID: str = "cn-shanghai"
    ALIYUN_ICE_OUTPUT_PATH: str = "video_translation/output"

    # ATA Configuration for subtitle extraction
    ATA_APPID: str
    ATA_ACCESS_TOKEN: str

    # VolcEngine Configuration for subtitle erasure and audio separation
    VOLCENGINE_API_KEY: str

    # Backend Callback Configuration
    BACKEND_URL: Optional[str] = None
    CALLBACK_API_KEY: Optional[str] = None

    # ElevenLabs Configuration for custom voices
    ELEVENLABS_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
