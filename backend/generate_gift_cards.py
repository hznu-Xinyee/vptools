#!/usr/bin/env python3
"""
点卡生成脚本
一次生成四种面额的点卡：100、1000、5000、50000积分
点卡有效期为7天
"""

import os
import sys
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.gift_card import GiftCard
from app.core.database import Base


def get_database_url():
    """从环境变量或.env文件获取数据库URL"""
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    if key.strip() == "DATABASE_URL":
                        return value.strip().strip('"').strip("'")

    raise RuntimeError("DATABASE_URL is not set")


def generate_card_code(length=16):
    """生成随机卡密"""
    # 使用大写字母和数字，排除容易混淆的字符（0, O, I, 1）
    chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
    return ''.join(secrets.choice(chars) for _ in range(length))


def create_gift_cards(db_session):
    """创建四种面额的点卡"""
    # 点卡面额
    denominations = [100, 1000, 5000, 50000]

    # 有效期：7天
    expires_at = datetime.utcnow() + timedelta(days=7)

    created_cards = []

    for points in denominations:
        # 生成唯一的卡密
        while True:
            card_code = generate_card_code()
            # 检查是否已存在
            existing = db_session.query(GiftCard).filter(
                GiftCard.card_code == card_code
            ).first()
            if not existing:
                break

        # 创建点卡
        gift_card = GiftCard(
            card_code=card_code,
            points=points,
            expires_at=expires_at
        )

        db_session.add(gift_card)
        created_cards.append({
            'code': card_code,
            'points': points,
            'expires_at': expires_at
        })

    db_session.commit()

    return created_cards


def main():
    print("=" * 60)
    print("点卡生成脚本")
    print("=" * 60)

    # 连接数据库
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 确保表已创建
        Base.metadata.create_all(bind=engine)

        print("\n正在生成点卡...")
        cards = create_gift_cards(db)

        print("\n✓ 点卡生成成功！\n")
        print("=" * 60)
        print(f"{'面额（积分）':<15} {'卡密':<20} {'有效期'}")
        print("=" * 60)

        for card in cards:
            expires_str = card['expires_at'].strftime('%Y-%m-%d %H:%M')
            print(f"{card['points']:<15} {card['code']:<20} {expires_str}")

        print("=" * 60)
        print(f"\n说明：")
        print(f"  - 点卡有效期为 7 天")
        print(f"  - 10 积分 = 1 RMB")
        print(f"  - 100 积分 = 10 元")
        print(f"  - 1000 积分 = 100 元")
        print(f"  - 5000 积分 = 500 元")
        print(f"  - 50000 积分 = 5000 元")
        print("\n请妥善保管卡密，每个卡密只能使用一次。\n")

        db.close()
        return 0

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
