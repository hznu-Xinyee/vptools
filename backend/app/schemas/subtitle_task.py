from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.subtitle_task import TaskStatus


class SubtitleTaskCreate(BaseModel):
    original_filename: str = Field(..., description="Original filename of the uploaded video")


class SubtitleTaskUpdate(BaseModel):
    oss_key: Optional[str] = None
    oss_url: Optional[str] = None
    volcengine_task_id: Optional[str] = None
    result_video_url: Optional[str] = None
    result_duration: Optional[int] = None
    status: Optional[TaskStatus] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class SubtitleTaskResponse(BaseModel):
    id: int
    user_id: int
    original_filename: str
    oss_key: Optional[str]
    oss_url: Optional[str]
    volcengine_task_id: Optional[str]
    result_video_url: Optional[str]
    result_duration: Optional[int]
    status: TaskStatus
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SubtitleTaskSubmitRequest(BaseModel):
    video_url: str = Field(..., description="Signed OSS URL of the uploaded video")
    oss_key: str = Field(..., description="OSS key of the uploaded video")
    original_filename: str = Field(..., description="Original filename of the video")
    mode: str = Field(default="Subtitle", description="Subtitle erasure mode: Subtitle or Text")


class SubtitleTaskSubmitResponse(BaseModel):
    task_id: int
    volcengine_task_id: str
    status: TaskStatus
