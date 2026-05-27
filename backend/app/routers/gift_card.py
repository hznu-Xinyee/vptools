import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.gift_card import GiftCard
from app.schemas.gift_card import GiftCardRedeem, RedeemResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/gift-cards/redeem", response_model=RedeemResponse)
def redeem_gift_card(
    redeem_data: GiftCardRedeem,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """兑换点卡"""
    # 查找点卡
    gift_card = db.query(GiftCard).filter(
        GiftCard.card_code == redeem_data.card_code
    ).first()

    if not gift_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="点卡不存在或卡密错误"
        )

    # 检查是否已使用
    if gift_card.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该点卡已被使用"
        )

    # 检查是否过期
    if gift_card.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该点卡已过期"
        )

    # 兑换点卡
    gift_card.is_used = True
    gift_card.used_by_user_id = current_user.id
    gift_card.used_at = datetime.utcnow()

    # 增加用户积分
    current_user.points += gift_card.points

    db.commit()
    db.refresh(current_user)

    logger.info(f"User {current_user.id} redeemed gift card {gift_card.card_code} for {gift_card.points} points")

    return RedeemResponse(
        message="兑换成功",
        points_added=gift_card.points,
        new_balance=current_user.points
    )
