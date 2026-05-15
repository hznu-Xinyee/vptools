"""
Script to delete all history records from the database.
This will delete all records from:
- video_translation_tasks
- subtitle_extract_tasks
- subtitle_tasks
"""

import sys
from app.core.database import SessionLocal
from app.models.video_translation import VideoTranslationTask
from app.models.subtitle_extract import SubtitleExtractTask
from app.models.subtitle_task import SubtitleTask


def clear_all_history():
    """Delete all history records from the database"""
    db = SessionLocal()
    try:
        print("Starting to delete all history records...")
        
        # Delete video translation tasks
        video_tasks = db.query(VideoTranslationTask).all()
        video_count = len(video_tasks)
        for task in video_tasks:
            db.delete(task)
        print(f"Deleted {video_count} video translation tasks")
        
        # Delete subtitle extract tasks
        extract_tasks = db.query(SubtitleExtractTask).all()
        extract_count = len(extract_tasks)
        for task in extract_tasks:
            db.delete(task)
        print(f"Deleted {extract_count} subtitle extract tasks")
        
        # Delete subtitle tasks
        subtitle_tasks = db.query(SubtitleTask).all()
        subtitle_count = len(subtitle_tasks)
        for task in subtitle_tasks:
            db.delete(task)
        print(f"Deleted {subtitle_count} subtitle tasks")
        
        db.commit()
        print("All history records deleted successfully!")
        print(f"Total deleted: {video_count + extract_count + subtitle_count} records")
        
    except Exception as e:
        db.rollback()
        print(f"Error deleting records: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    confirm = input("Are you sure you want to delete ALL history records? This cannot be undone. Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        clear_all_history()
    else:
        print("Operation cancelled.")
