from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CustomVoiceBase(BaseModel):
    name: str
    voice_id: str
    language: str
    gender: str
    description: Optional[str] = None


class CustomVoiceCreate(CustomVoiceBase):
    pass


class CustomVoiceUpdate(BaseModel):
    name: Optional[str] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CustomVoiceResponse(CustomVoiceBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
