from app.routers.auth import router as auth_router
from app.routers.subtitle_task import router as subtitle_task_router
from app.routers.subtitle_extract import router as subtitle_extract_router
from app.routers.video_translation import router as video_translation_router

__all__ = ["auth_router", "subtitle_task_router", "subtitle_extract_router", "video_translation_router"]
