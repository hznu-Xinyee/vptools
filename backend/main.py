from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, Response
import logging
from app.core.database import engine, Base
from app.routers import auth_router, subtitle_task_router, subtitle_extract_router, video_translation_router

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

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


@app.get("/")
def read_root():
    return {"message": "Welcome to VP Backend API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
