from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_tags_column():
    """Ensure the tags column exists in video_translation_tasks table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('video_translation_tasks')]
    
    if 'tags' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE video_translation_tasks ADD COLUMN tags TEXT"))
            conn.commit()
            print("Added 'tags' column to video_translation_tasks table")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
