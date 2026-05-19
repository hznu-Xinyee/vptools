from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class CustomVoice(Base):
    __tablename__ = "custom_voices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    voice_id = Column(String, nullable=False)  # ElevenLabs voice_id
    language = Column(String, nullable=False)  # Language code (zh, en, yue, etc.)
    gender = Column(String, nullable=False)  # male, female, or other
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
