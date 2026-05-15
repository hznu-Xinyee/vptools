from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    points = Column(Integer, default=0)
    
    subtitle_tasks = relationship("SubtitleTask", back_populates="user")
    subtitle_extract_tasks = relationship("SubtitleExtractTask", back_populates="user")
    video_translation_tasks = relationship("VideoTranslationTask", back_populates="user")
