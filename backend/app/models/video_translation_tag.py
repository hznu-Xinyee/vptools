from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class VideoTranslationTag(Base):
    __tablename__ = "video_translation_tags"
    __table_args__ = (
        UniqueConstraint("user_id", "normalized_name", name="uq_video_translation_tags_user_normalized_name"),
        Index("ix_video_translation_tags_user_id", "user_id"),
        Index("ix_video_translation_tags_user_updated_at", "user_id", "updated_at"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    normalized_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")
    task_links = relationship("VideoTranslationTaskTag", back_populates="tag", cascade="all, delete-orphan")


class VideoTranslationTaskTag(Base):
    __tablename__ = "video_translation_task_tags"
    __table_args__ = (
        UniqueConstraint("task_id", "tag_id", name="uq_video_translation_task_tags_task_tag"),
        Index("ix_video_translation_task_tags_task_id", "task_id"),
        Index("ix_video_translation_task_tags_tag_id", "tag_id"),
        Index("ix_video_translation_task_tags_tag_created_at", "tag_id", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("video_translation_tasks.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(Integer, ForeignKey("video_translation_tags.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    task = relationship("VideoTranslationTask", back_populates="tag_links")
    tag = relationship("VideoTranslationTag", back_populates="task_links")
