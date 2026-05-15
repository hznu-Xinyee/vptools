from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.subtitle_extract import ExtractStatus


class SubtitleExtractCreate(BaseModel):
    original_filename: str = Field(..., description="Original filename of the uploaded file")
    source_type: str = Field(..., description="Source type: video, audio, or history_video")
    source_oss_key: Optional[str] = Field(None, description="OSS key of the source file")


class SubtitleExtractResponse(BaseModel):
    id: int
    user_id: int
    original_filename: str
    source_type: str
    source_oss_key: Optional[str]
    audio_oss_key: Optional[str]
    audio_oss_url: Optional[str]
    ata_task_id: Optional[str]
    status: ExtractStatus
    subtitle_result: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SubtitleExtractSubmitRequest(BaseModel):
    oss_key: str = Field(..., description="OSS key of the uploaded file")
    original_filename: str = Field(..., description="Original filename of the file")
    source_type: str = Field(default="video", description="Source type: video, audio, or history_video")
    history_task_id: Optional[int] = Field(None, description="ID of the history task if source_type is history_video")


class SubtitleExtractSubmitResponse(BaseModel):
    task_id: int
    ata_task_id: Optional[str]
    status: ExtractStatus
