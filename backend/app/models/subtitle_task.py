from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SubtitleTask(Base):
    __tablename__ = "subtitle_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Video information
    original_filename = Column(String, nullable=False)
    oss_key = Column(String, nullable=True)  # OSS storage key
    oss_url = Column(String, nullable=True)  # Signed OSS URL
    
    # VolcEngine task information
    volcengine_task_id = Column(String, nullable=True)
    
    # Result information
    result_video_url = Column(String, nullable=True)
    result_duration = Column(Integer, nullable=True)
    
    # Task status
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="subtitle_tasks")
