from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from app.models.video_translation import VideoTranslationStatus


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


class VideoTranslationSubmitRequest(BaseModel):
    video_oss_key: str = Field(..., description="OSS key of the uploaded video")
    media_id: Optional[str] = Field(None, description="ICE media ID of the uploaded video")
    video_url: Optional[str] = Field(None, description="URL of the uploaded video")
    original_filename: str = Field(..., description="Original video filename")
    target_language: str = Field(..., description="Target translation language")
    subtitle_source_type: str = Field(default="upload", description="upload or extract_history")
    subtitle_json: Optional[Any] = Field(None, description="Subtitle JSON data")
    subtitle_extract_task_id: Optional[int] = Field(None, description="Subtitle extraction task ID")
    subtitle_params: Optional[SubtitleParams] = None


class VideoTranslationSubmitResponse(BaseModel):
    task_id: int
    docker_task_id: Optional[str]
    status: VideoTranslationStatus
