from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, Response
from fastapi.staticfiles import StaticFiles
import logging
import os
from app.core.database import engine, Base, ensure_tags_column
from app.routers import auth_router, subtitle_task_router, subtitle_extract_router, video_translation_router
from app.routers.custom_voice import router as custom_voice_router

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)
ensure_tags_column()

app = FastAPI(title="VP Backend", version="1.0.0")


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    # Handle OPTIONS requests globally
    if request.method == "OPTIONS":
        response = Response(status_code=200)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(subtitle_task_router, prefix="/api/subtitle", tags=["subtitle"])
app.include_router(subtitle_extract_router, prefix="/api/subtitle-extract", tags=["subtitle-extract"])
app.include_router(video_translation_router, prefix="/api/video-translation", tags=["video-translation"])
app.include_router(custom_voice_router, prefix="/api", tags=["custom-voice"])

# Mount static files for voice previews
HELLO_VOICES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "public", "hello_voices")
if os.path.exists(HELLO_VOICES_DIR):
    app.mount("/api/hello-voices", StaticFiles(directory=HELLO_VOICES_DIR), name="hello-voices")


@app.get("/")
def read_root():
    return {"message": "Welcome to VP Backend API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
