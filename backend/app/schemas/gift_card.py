from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GiftCardRedeem(BaseModel):
    card_code: str


class GiftCardResponse(BaseModel):
    id: int
    card_code: str
    points: int
    is_used: bool
    used_by_user_id: Optional[int] = None
    used_at: Optional[datetime] = None
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class RedeemResponse(BaseModel):
    message: str
    points_added: int
    new_balance: int
