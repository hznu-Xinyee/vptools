from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


class VideoTranslationStatus(str, enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoTranslationTask(Base):
    __tablename__ = "video_translation_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    video_oss_key = Column(String, nullable=False)
    video_url = Column(String, nullable=True)
    original_video_url = Column(String, nullable=True)
    subtitle_source_type = Column(String, nullable=False)
    subtitle_extract_task_id = Column(Integer, nullable=True)
    subtitle_json = Column(Text, nullable=False)
    target_language = Column(String, nullable=False)
    target_languages = Column(Text, nullable=True)
    docker_task_id = Column(String, nullable=True)
    status = Column(SQLEnum(VideoTranslationStatus), default=VideoTranslationStatus.PROCESSING, nullable=False)
    timeline_json = Column(Text, nullable=True)
    tts_timestamps = Column(Text, nullable=True)
    result_video_url = Column(String, nullable=True)
    language_results_json = Column(Text, nullable=True)
    error_message = Column(String, nullable=True)
    is_auto = Column(Boolean, default=False, nullable=False)
    current_stage = Column(String, nullable=True)  # For auto translation: subtitle_extraction, subtitle_erasure, video_translation
    background_audio_url = Column(String, nullable=True)  # Background audio after music demix
    charged_points = Column(Integer, default=0, nullable=False)
    points_refunded = Column(Boolean, default=False, nullable=False)
    tags = Column(Text, nullable=True)
    custom_voice_id = Column(Integer, nullable=True)  # Custom voice ID if using ElevenLabs
    refunded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="video_translation_tasks")
    tag_links = relationship(
        "VideoTranslationTaskTag",
        back_populates="task",
        cascade="all, delete-orphan",
    )
