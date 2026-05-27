from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.core.database import Base


class GiftCard(Base):
    __tablename__ = "gift_cards"

    id = Column(Integer, primary_key=True, index=True)
    card_code = Column(String, unique=True, index=True, nullable=False)  # 点卡卡密
    points = Column(Integer, nullable=False)  # 点卡面额（积分）
    is_used = Column(Boolean, default=False)  # 是否已使用
    used_by_user_id = Column(Integer, nullable=True)  # 使用者用户ID
    used_at = Column(DateTime, nullable=True)  # 使用时间
    expires_at = Column(DateTime, nullable=False)  # 过期时间
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间
