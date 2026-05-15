from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


class ExtractStatus(str, enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SubtitleExtractTask(Base):
    __tablename__ = "subtitle_extract_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # "video", "audio", "history_video"
    source_oss_key = Column(String, nullable=True)  # Original file OSS key
    audio_oss_key = Column(String, nullable=True)  # Converted audio OSS key
    audio_oss_url = Column(String, nullable=True)  # Converted audio OSS URL
    ata_task_id = Column(String, nullable=True)  # ATA task ID
    status = Column(SQLEnum(ExtractStatus), default=ExtractStatus.PROCESSING, nullable=False)
    subtitle_result = Column(Text, nullable=True)  # JSON string of subtitle result
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="subtitle_extract_tasks")
