from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SubtitleItem(BaseModel):
    start_time: int
    end_time: int
    text: str
    words: Optional[List[Dict[str, Any]]] = None


class SubtitleParams(BaseModel):
    alignment: Optional[str] = Field("BottomCenter", description="Subtitle alignment")
    font: Optional[str] = Field(None, description="Subtitle font family")
    font_size: Optional[int] = Field(42, description="Subtitle font size")
    font_color: Optional[str] = Field("#ffffff", description="Subtitle font color")
    outline: Optional[int] = Field(2, description="Subtitle outline width")
    outline_colour: Optional[str] = Field("#000000", description="Subtitle outline color")
    back_colour: Optional[str] = Field(None, description="Subtitle back color")
    effect_color_style: Optional[str] = Field(None, description="ICE effect color style")
    subtitle_effects: Optional[List[Dict[str, Any]]] = Field(None, description="ICE subtitle effects")
    adapt_mode: Optional[str] = Field("Auto", description="Subtitle adapt mode (Auto for auto-wrap)")
    y: Optional[float] = Field(None, description="Subtitle vertical position")


class TranslateVideoRequest(BaseModel):
    task_id: int
    media_id: str = Field(..., description="Video OSS key or media id")
    subtitle_json: List[SubtitleItem]
    target_language: str
    subtitle_params: Optional[SubtitleParams] = None
    background_audio_media_id: Optional[str] = Field(None, description="Background audio media ID after music demix")
    background_audio_url: Optional[str] = Field(None, description="Background audio URL after music demix")
    custom_voice_id: Optional[str] = Field(None, description="Custom ElevenLabs voice ID")
    continuous_dubbing: bool = False


class TranslateVideoResponse(BaseModel):
    task_id: int
    docker_task_id: str
    status: str
    timeline_json: Optional[Dict[str, Any]] = None
    result_video_url: Optional[str] = None
    audio_segments: Optional[List[Dict[str, Any]]] = None
    tts_timestamps: Optional[List[Dict[str, Any]]] = None
    summary_path: Optional[str] = None
    message: Optional[str] = None


class AutoTranslationRequest(BaseModel):
    task_id: int
    oss_key: str
    file_url: str
    original_filename: str
    target_language: Optional[str] = None
    target_languages: Optional[List[str]] = None
    skip_subtitle_erasure: bool = False
    custom_voice_id: Optional[str] = Field(None, description="Custom ElevenLabs voice ID (deprecated, use custom_voice_map)")
    custom_voice_map: Optional[Dict[str, str]] = Field(None, description="Map of language code to custom voice ID")
    subtitle_params: Optional[SubtitleParams] = None
    continuous_dubbing: bool = False


class AutoTranslationResponse(BaseModel):
    task_id: int
    status: str
    language_results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
