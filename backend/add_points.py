from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    users = db.query(User).all()
    for user in users:
        user.points = user.points + 10000
        print(f"Updated user {user.username}: points = {user.points}")
    db.commit()
    print(f"Updated {len(users)} users with +10000 points")
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
