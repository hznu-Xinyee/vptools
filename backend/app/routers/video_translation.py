from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import logging
import io
import json
import asyncio
import os
import re
import tempfile
import zipfile
from urllib.parse import unquote, urlparse
import requests

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.subtitle_extract import SubtitleExtractTask, ExtractStatus
from app.models.subtitle_task import SubtitleTask, TaskStatus
from app.models.video_translation import VideoTranslationTask, VideoTranslationStatus
from app.models.video_translation_tag import VideoTranslationTag, VideoTranslationTaskTag
from app.schemas.video_translation import SubtitleParams, VideoTranslationSubmitRequest, VideoTranslationSubmitResponse
from app.services.oss_service import oss_service
from app.services.ice_service import ice_service
from app.services.video_translation_service import video_translation_service


class RegisterMediaRequest(BaseModel):
    oss_key: str
    file_url: str


class CreateRecordRequest(BaseModel):
    original_filename: str
    target_language: str
    oss_key: str
    status: str = "processing"
    is_auto: bool = False


class UpdateStageRequest(BaseModel):
    current_stage: str


class UpdateTaskNameRequest(BaseModel):
    original_filename: str


class FcCallbackRequest(BaseModel):
    task_id: int
    status: str
    language_results: Optional[Dict[str, Any]] = None
    result_video_url: Optional[str] = None
    error_message: Optional[str] = None


class DownloadSelectionItem(BaseModel):
    task_id: int
    language_code: Optional[str] = None
    filename: Optional[str] = None


class DownloadSelectedRequest(BaseModel):
    items: List[DownloadSelectionItem]


logger = logging.getLogger(__name__)
router = APIRouter()
fc_submit_semaphore = asyncio.Semaphore(10)


def _build_backend_auto_subtitle_params(subtitle_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    params = {
        "alignment": "TopCenter",
        "font": "Alibaba PuHuiTi",
        "font_size": 80,
        "font_color": "#ffffff",
        "outline": 2,
        "outline_colour": "#000000",
        "y": 0.75
    }
    params.update({key: value for key, value in (subtitle_params or {}).items() if value is not None})
    return params


def _normalize_target_languages(target_language: Optional[str], target_languages: Optional[List[str]]) -> List[str]:
    raw_languages = target_languages if target_languages is not None else ([target_language] if target_language else [])
    languages = []
    seen = set()
    for language in raw_languages:
        normalized = str(language).strip() if language is not None else ""
        if normalized and normalized not in seen:
            languages.append(normalized)
            seen.add(normalized)

    if not languages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请至少选择一种目标语言")

    return languages


def _calculate_auto_translation_points(target_languages: List[str]) -> int:
    return 10 + max(0, len(target_languages) - 1) * 5


def _json_loads(value: Optional[str], fallback: Any):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _normalize_tag_name(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())[:100]


def _normalize_tag_key(value: Any) -> str:
    return _normalize_tag_name(value).lower()


def _normalize_tag_list(tags: Optional[List[str]]) -> List[str]:
    normalized_tags = []
    seen = set()
    for tag in tags or []:
        tag_name = _normalize_tag_name(tag)
        tag_key = _normalize_tag_key(tag_name)
        if not tag_name or tag_key in seen:
            continue
        normalized_tags.append(tag_name)
        seen.add(tag_key)
    return normalized_tags


def _sync_video_translation_task_tags(db: Session, task: VideoTranslationTask, raw_tags: Optional[List[str]]) -> List[str]:
    normalized_tags = _normalize_tag_list(raw_tags)
    task.tags = json.dumps(normalized_tags, ensure_ascii=False) if normalized_tags else None

    db.query(VideoTranslationTaskTag).filter(VideoTranslationTaskTag.task_id == task.id).delete()
    for tag_name in normalized_tags:
        normalized_name = _normalize_tag_key(tag_name)
        tag_id = db.execute(
            pg_insert(VideoTranslationTag)
            .values(
                user_id=task.user_id,
                name=tag_name,
                normalized_name=normalized_name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            .on_conflict_do_update(
                constraint="uq_video_translation_tags_user_normalized_name",
                set_={"updated_at": datetime.utcnow()},
            )
            .returning(VideoTranslationTag.id)
        ).scalar_one()

        db.add(VideoTranslationTaskTag(task_id=task.id, tag_id=tag_id))

    return normalized_tags


def _get_task_target_languages(task: VideoTranslationTask) -> List[str]:
    languages = _json_loads(task.target_languages, [])
    if isinstance(languages, list) and languages:
        return languages
    return [task.target_language] if task.target_language else []


def _get_task_language_results(task: VideoTranslationTask) -> Dict[str, Any]:
    results = _json_loads(task.language_results_json, {})
    if isinstance(results, dict):
        return results
    return {}


def _json_default(value: Any):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _model_dump_exclude_none(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)


def _safe_download_filename(filename: Optional[str], fallback: str) -> str:
    raw_name = os.path.basename((filename or fallback).strip()) or fallback
    safe_name = re.sub(r'[\\/:*?"<>|\r\n]+', "_", raw_name).strip(" .")
    return safe_name or fallback


def _get_download_extension(url: Optional[str]) -> str:
    if not url:
        return "mp4"
    path = unquote(urlparse(url).path)
    extension = os.path.splitext(path)[1].lstrip(".").lower()
    if re.fullmatch(r"[a-z0-9]{2,5}", extension):
        return extension
    return "mp4"


def _build_video_translation_download_filename(
    task: VideoTranslationTask,
    language_code: Optional[str],
    result_url: str,
    requested_filename: Optional[str]
) -> str:
    extension = _get_download_extension(result_url)
    base_name = os.path.splitext(task.original_filename or f"task_{task.id}")[0]
    language_suffix = language_code or task.target_language or "translation"
    fallback = f"{base_name}_{language_suffix}.{extension}"
    filename = _safe_download_filename(requested_filename, fallback)
    if not os.path.splitext(filename)[1]:
        filename = f"{filename}.{extension}"
    return filename


def _unique_zip_filename(filename: str, used_names: set[str]) -> str:
    base_name, extension = os.path.splitext(filename)
    candidate = filename
    index = 2
    while candidate in used_names:
        candidate = f"{base_name}_{index}{extension}"
        index += 1
    used_names.add(candidate)
    return candidate


def _set_task_language_results(task: VideoTranslationTask, language_results: Dict[str, Any]) -> None:
    task.language_results_json = json.dumps(language_results, ensure_ascii=False, default=_json_default)


def _language_results_for_response(task: VideoTranslationTask) -> Dict[str, Any]:
    results = _get_task_language_results(task)
    if results:
        # Exclude timeline_json and tts_timestamps to reduce response size
        clean_results = {}
        for lang_code, lang_result in results.items():
            if isinstance(lang_result, dict):
                clean_result = {k: v for k, v in lang_result.items() if k not in ('timeline_json', 'tts_timestamps')}
                clean_results[lang_code] = clean_result
            else:
                clean_results[lang_code] = lang_result
        return clean_results

    if not task.target_language:
        return {}

    result = {
        "status": task.status.value,
        "docker_task_id": task.docker_task_id,
        "result_video_url": task.result_video_url,
        "error_message": task.error_message,
    }
    return {task.target_language: result}


def _serialize_video_translation_task(task: VideoTranslationTask) -> Dict[str, Any]:
    return {
        "id": task.id,
        "original_filename": task.original_filename,
        "target_language": task.target_language,
        "target_languages": _get_task_target_languages(task),
        "docker_task_id": task.docker_task_id,
        "status": task.status.value,
        "result_video_url": task.result_video_url,
        "original_video_url": task.original_video_url,
        "language_results": _language_results_for_response(task),
        "error_message": task.error_message,
        "is_auto": task.is_auto,
        "current_stage": task.current_stage,
        "charged_points": task.charged_points or 0,
        "points_refunded": bool(task.points_refunded),
        "tags": _json_loads(task.tags, []),
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


def _refund_translation_points(db: Session, task: VideoTranslationTask) -> None:
    charged_points = task.charged_points or 0
    if charged_points <= 0 or task.points_refunded:
        return

    user = db.query(User).filter(User.id == task.user_id).first()
    if user:
        user.points += charged_points
        logger.info(
            "[自动翻译] 任务 %s 失败，返还%s积分给用户 %s，当前积分: %s",
            task.id,
            charged_points,
            user.id,
            user.points,
        )
    task.points_refunded = True
    task.refunded_at = datetime.utcnow()


@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        content = await file.read()
        oss_key = oss_service.generate_upload_key(file.filename, current_user.id)
        oss_service.upload_file(oss_key, io.BytesIO(content), content_type=file.content_type)
        file_url = oss_service.get_file_url(oss_key)
        media_id = ice_service.register_media(file_url, oss_key, "video")
        return {"oss_key": oss_key, "file_url": file_url, "media_id": media_id}
    except Exception as e:
        logger.error(f"Video translation upload failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/upload-video-multipart")
async def upload_video_multipart(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        import uuid
        upload_id = uuid.uuid4().hex
        oss_key = oss_service.generate_upload_key(file.filename, current_user.id)
        file_url = oss_service.upload_file_multipart(file, oss_key, upload_id)
        media_id = ice_service.register_media(file_url, oss_key, "video")
        return {"oss_key": oss_key, "file_url": file_url, "media_id": media_id, "upload_id": upload_id}
    except Exception as e:
        logger.error(f"Video translation multipart upload failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/upload-progress/{upload_id}")
async def get_upload_progress(upload_id: str):
    from app.services.oss_service import upload_progress
    if upload_id not in upload_progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    return upload_progress[upload_id]


@router.get("/oss-config")
async def get_oss_config(current_user: User = Depends(get_current_user)):
    """Get OSS configuration for frontend direct upload (development only)"""
    return {
        "region": settings.OSS_REGION_NAME or "oss-cn-shanghai",
        "accessKeyId": settings.OSS_ACCESS_KEY_ID,
        "accessKeySecret": settings.OSS_ACCESS_KEY_SECRET,
        "bucket": settings.OSS_BUCKET_NAME,
        "endpoint": settings.OSS_ENDPOINT.replace("https://", "")
    }


@router.post("/register-media")
async def register_media(
    request: RegisterMediaRequest,
    current_user: User = Depends(get_current_user)
):
    """Register uploaded media with ICE and return media_id"""
    try:
        media_id = ice_service.register_media(request.file_url, request.oss_key, "video")
        return {"media_id": media_id}
    except Exception as e:
        logger.error(f"Register media failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/create-record")
async def create_video_translation_record(
    request: CreateRecordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a video translation record immediately without submitting to Docker"""
    try:
        task = VideoTranslationTask(
            user_id=current_user.id,
            original_filename=request.original_filename,
            video_oss_key=request.oss_key,
            subtitle_source_type="auto",  # For auto translation workflow
            subtitle_json=json.dumps([]),  # Empty array as default, will be updated later
            target_language=request.target_language,
            status=VideoTranslationStatus.PROCESSING,
            is_auto=request.is_auto,
            current_stage="subtitle_extraction"  # Initial stage
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return {
            "task_id": task.id,
            "status": task.status.value
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Create video translation record failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/tasks/{task_id}/stage")
async def update_task_stage(
    task_id: int,
    request: UpdateStageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the current stage of a video translation task"""
    try:
        task = db.query(VideoTranslationTask).filter(
            VideoTranslationTask.id == task_id,
            VideoTranslationTask.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
        task.current_stage = request.current_stage
        db.commit()
        db.refresh(task)
        
        return {
            "task_id": task.id,
            "current_stage": task.current_stage
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Update task stage failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


class AutoTranslationSubmitRequest(BaseModel):
    original_filename: str
    target_language: Optional[str] = None
    target_languages: Optional[List[str]] = None
    oss_key: str
    file_url: str
    original_video_url: Optional[str] = None
    skip_subtitle_erasure: bool = False
    full_screen_erase: bool = True
    hide_subtitles: bool = False
    subtitle_params: Optional[SubtitleParams] = None
    tags: Optional[List[str]] = None
    custom_voice_id: Optional[int] = None
    custom_voice_map: Optional[Dict[str, Optional[str]]] = None  # Map language code to voice_id string (ElevenLabs voice_id or None for default)
    continuous_dubbing: bool = False
    use_test_version: bool = False


async def submit_auto_translation_to_fc_background(
    task_id: int,
    oss_key: str,
    file_url: str,
    original_filename: str,
    target_language: Optional[str],
    target_languages: List[str],
    skip_subtitle_erasure: bool,
    full_screen_erase: bool,
    hide_subtitles: bool,
    subtitle_params: Optional[Dict[str, Any]],
    custom_voice_id: Optional[int] = None,
    custom_voice_map: Optional[Dict[str, Optional[str]]] = None,  # Map language code to voice_id string
    continuous_dubbing: bool = False,
    use_test_version: bool = False
):
    logger.info(f"[自动翻译] 任务 {task_id} 已进入 FC 提交队列，最多同时提交 10 个任务")
    async with fc_submit_semaphore:
        db = next(get_db())
        try:
            task = db.query(VideoTranslationTask).filter(VideoTranslationTask.id == task_id).first()
            if not task:
                logger.warning(f"[自动翻译] FC 提交前找不到任务 {task_id}")
                return

            if task.status != VideoTranslationStatus.PROCESSING:
                logger.info(f"[自动翻译] 任务 {task_id} 当前状态为 {task.status.value}，跳过 FC 提交")
                return

            # Get custom voice voice_id if custom_voice_id is provided
            custom_voice_voice_id = None
            if custom_voice_id:
                from app.models.custom_voice import CustomVoice
                # Remove user_id filter to allow shared custom voices across all users
                custom_voice = db.query(CustomVoice).filter(
                    CustomVoice.id == custom_voice_id,
                    CustomVoice.is_active == True
                ).first()
                if custom_voice:
                    custom_voice_voice_id = custom_voice.voice_id
                    task.custom_voice_id = custom_voice_id

            # Build custom_voice_voice_id_map from custom_voice_map
            # custom_voice_map now contains voice_id strings directly (not database IDs)
            custom_voice_voice_id_map = None
            if custom_voice_map:
                custom_voice_voice_id_map = {}
                logger.info(f"[自动翻译] 收到 custom_voice_map: {custom_voice_map}")
                for lang_code, voice_id in custom_voice_map.items():
                    # voice_id is now the ElevenLabs voice_id string (or None for default TTS)
                    if voice_id:
                        custom_voice_voice_id_map[lang_code] = voice_id
                        logger.info(f"[自动翻译] {lang_code} 使用自定义音色: {voice_id}")
                    else:
                        # None means use default TTS for this language
                        custom_voice_voice_id_map[lang_code] = None
                        logger.info(f"[自动翻译] {lang_code} 使用默认TTS")
                logger.info(f"[自动翻译] 最终 custom_voice_voice_id_map: {custom_voice_voice_id_map}")


            task.current_stage = "video_translation"
            db.commit()

            fc_response = await video_translation_service.submit_auto_translation(
                task_id=task_id,
                oss_key=oss_key,
                file_url=file_url,
                original_filename=original_filename,
                target_language=target_language,
                target_languages=target_languages,
                custom_voice_id=custom_voice_voice_id,
                custom_voice_id_map=custom_voice_voice_id_map,
                skip_subtitle_erasure=skip_subtitle_erasure,
                full_screen_erase=full_screen_erase,
                hide_subtitles=hide_subtitles,
                subtitle_params=subtitle_params,
                continuous_dubbing=continuous_dubbing,
                use_test_version=use_test_version
            )
            logger.info(f"[自动翻译] 任务 {task_id} 已提交到 FC 服务，响应: {fc_response}")
            
            # Update language_results from FC response
            if fc_response and 'language_results' in fc_response:
                task.language_results_json = json.dumps(fc_response['language_results'], ensure_ascii=False, default=_json_default)
                db.commit()
        except Exception as submit_error:
            logger.error(f"[自动翻译] 任务 {task_id} 提交到 FC 服务失败: {str(submit_error)}", exc_info=True)
            db.rollback()
            try:
                task = db.query(VideoTranslationTask).filter(VideoTranslationTask.id == task_id).first()
                if task:
                    task.status = VideoTranslationStatus.FAILED
                    task.error_message = f"提交到视频翻译服务失败: {str(submit_error)}"
                    task.current_stage = None
                    _refund_translation_points(db, task)
                    db.commit()
            except Exception as db_error:
                logger.error(f"[自动翻译] 更新任务 {task_id} 提交失败状态失败: {str(db_error)}", exc_info=True)
                db.rollback()
        finally:
            db.close()


@router.post("/submit-auto")
async def submit_auto_translation(
    request: AutoTranslationSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit auto translation task (async processing in background)"""
    try:
        target_languages = _normalize_target_languages(request.target_language, request.target_languages)
        required_points = _calculate_auto_translation_points(target_languages)
        if current_user.points < required_points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"积分不足，需要 {required_points} 积分，当前积分: {current_user.points}"
            )

        language_results = {
            language: {"status": "pending"}
            for language in target_languages
        }

        current_user.points -= required_points

        # Create record
        task = VideoTranslationTask(
            user_id=current_user.id,
            original_filename=request.original_filename,
            video_oss_key=request.oss_key,
            original_video_url=request.original_video_url,
            subtitle_source_type="auto",
            subtitle_json=json.dumps([]),
            target_language=target_languages[0],
            target_languages=json.dumps(target_languages, ensure_ascii=False),
            language_results_json=json.dumps(language_results, ensure_ascii=False, default=_json_default),
            charged_points=required_points,
            status=VideoTranslationStatus.PROCESSING,
            is_auto=True,
            current_stage="queued"
        )
        db.add(task)
        db.flush()
        _sync_video_translation_task_tags(db, task, request.tags)
        db.commit()
        db.refresh(task)
        
        request_subtitle_params = _model_dump_exclude_none(request.subtitle_params) if request.subtitle_params else None
        subtitle_params = _build_backend_auto_subtitle_params(request_subtitle_params)

        asyncio.create_task(submit_auto_translation_to_fc_background(
            task.id,
            request.oss_key,
            request.file_url,
            request.original_filename,
            request.target_language,
            target_languages,
            request.skip_subtitle_erasure,
            request.full_screen_erase,
            request.hide_subtitles,
            subtitle_params,
            request.custom_voice_id,
            request.custom_voice_map,
            request.continuous_dubbing,
            request.use_test_version
        ))

        return {
            "task_id": task.id,
            "status": task.status.value,
            "target_languages": target_languages,
            "charged_points": required_points,
            "message": "任务已提交，正在排队等待 FC 处理"
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Submit auto translation failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/submit", response_model=VideoTranslationSubmitResponse)
async def submit_video_translation_task(
    task_data: VideoTranslationSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Check and deduct points for manual translation (not auto)
        if not task_data.is_auto:
            required_points = 5
            if current_user.points < required_points:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"积分不足，需要 {required_points} 积分，当前积分: {current_user.points}"
                )
            current_user.points -= required_points
        
        subtitle_data = task_data.subtitle_json
        if task_data.subtitle_source_type == "extract_history":
            extract_task = db.query(SubtitleExtractTask).filter(
                SubtitleExtractTask.id == task_data.subtitle_extract_task_id,
                SubtitleExtractTask.user_id == current_user.id,
                SubtitleExtractTask.status == ExtractStatus.COMPLETED
            ).first()
            if not extract_task or not extract_task.subtitle_result:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subtitle extraction task not found")
            subtitle_data = json.loads(extract_task.subtitle_result).get("utterances", [])

        if not subtitle_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subtitle JSON is required")
        if not task_data.media_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Video media ID is required")

        task = VideoTranslationTask(
            user_id=current_user.id,
            original_filename=task_data.original_filename,
            video_oss_key=task_data.video_oss_key,
            video_url=task_data.video_url,
            subtitle_source_type=task_data.subtitle_source_type,
            subtitle_extract_task_id=task_data.subtitle_extract_task_id,
            subtitle_json=json.dumps(subtitle_data, ensure_ascii=False),
            target_language=task_data.target_language,
            status=VideoTranslationStatus.PROCESSING,
            is_auto=task_data.is_auto if hasattr(task_data, 'is_auto') else False
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Convert subtitle params to dict
        subtitle_params_dict = _model_dump_exclude_none(task_data.subtitle_params) if task_data.subtitle_params else None

        docker_response = await video_translation_service.submit_task(
            media_id=task_data.media_id,
            subtitle_json=subtitle_data,
            target_language=task.target_language,
            task_id=task.id,
            subtitle_params=subtitle_params_dict
        )
        task.docker_task_id = docker_response.get("docker_task_id") or docker_response.get("task_id")
        task.status = VideoTranslationStatus(docker_response.get("status", VideoTranslationStatus.PROCESSING.value))
        task.timeline_json = json.dumps(docker_response.get("timeline_json"), ensure_ascii=False) if docker_response.get("timeline_json") else None
        task.tts_timestamps = json.dumps(docker_response.get("tts_timestamps"), ensure_ascii=False) if docker_response.get("tts_timestamps") else None
        task.result_video_url = docker_response.get("result_video_url")
        if task.status == VideoTranslationStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(task)

        return VideoTranslationSubmitResponse(
            task_id=task.id,
            docker_task_id=task.docker_task_id,
            status=task.status
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Submit video translation task failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/tags")
async def get_video_translation_tags(
    q: Optional[str] = None,
    sort: str = "recent",
    limit: int = 10,
    is_auto: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    normalized_query = _normalize_tag_key(q) if q else ""
    safe_limit = min(max(limit, 1), 200)

    query = db.query(
        VideoTranslationTag.id,
        VideoTranslationTag.name,
        func.count(VideoTranslationTaskTag.task_id).label("usage_count"),
        func.max(VideoTranslationTask.created_at).label("last_used_at")
    ).join(
        VideoTranslationTaskTag,
        VideoTranslationTaskTag.tag_id == VideoTranslationTag.id
    ).join(
        VideoTranslationTask,
        VideoTranslationTask.id == VideoTranslationTaskTag.task_id
    ).filter(
        VideoTranslationTag.user_id == current_user.id,
        VideoTranslationTask.user_id == current_user.id
    )

    if is_auto is not None:
        query = query.filter(VideoTranslationTask.is_auto == is_auto)

    if normalized_query:
        query = query.filter(VideoTranslationTag.normalized_name.contains(normalized_query))

    query = query.group_by(VideoTranslationTag.id, VideoTranslationTag.name)

    total = query.count()
    if sort == "popular":
        query = query.order_by(func.count(VideoTranslationTaskTag.task_id).desc(), func.max(VideoTranslationTask.created_at).desc())
    elif sort == "name":
        query = query.order_by(VideoTranslationTag.name.asc())
    else:
        query = query.order_by(func.max(VideoTranslationTask.created_at).desc(), func.count(VideoTranslationTaskTag.task_id).desc())

    items = query.limit(safe_limit).all()
    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "usage_count": item.usage_count,
                "last_used_at": item.last_used_at.isoformat() if item.last_used_at else None,
            }
            for item in items
        ],
        "total": total,
    }


@router.get("/tasks")
async def get_video_translation_tasks(
    page: int = 1,
    page_size: int = 10,
    is_auto: bool = None,
    tags: Optional[str] = None,
    tag_id: Optional[int] = None,
    language: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if page_size < 1:
        page_size = 10
    elif page_size > 1000:
        page_size = 1000
    if page < 1:
        page = 1

    offset = (page - 1) * page_size
    query = db.query(VideoTranslationTask).filter(VideoTranslationTask.user_id == current_user.id)

    if is_auto is not None:
        query = query.filter(VideoTranslationTask.is_auto == is_auto)

    if language:
        query = query.filter(
            or_(
                VideoTranslationTask.target_language == language,
                VideoTranslationTask.target_languages.contains(f'"{language}"'),
                VideoTranslationTask.language_results_json.contains(f'"{language}"')
            )
        )
    
    if tag_id:
        query = query.join(
            VideoTranslationTaskTag,
            VideoTranslationTaskTag.task_id == VideoTranslationTask.id
        ).join(
            VideoTranslationTag,
            VideoTranslationTag.id == VideoTranslationTaskTag.tag_id
        ).filter(
            VideoTranslationTaskTag.tag_id == tag_id,
            VideoTranslationTag.user_id == current_user.id
        )
    
    if tags:
        normalized_tags = list(dict.fromkeys(
            _normalize_tag_key(tag)
            for tag in tags.split(',')
            if _normalize_tag_key(tag)
        ))
        if normalized_tags:
            tagged_task_ids = db.query(VideoTranslationTaskTag.task_id).join(
                VideoTranslationTag,
                VideoTranslationTag.id == VideoTranslationTaskTag.tag_id
            ).filter(
                VideoTranslationTag.user_id == current_user.id,
                VideoTranslationTag.normalized_name.in_(normalized_tags)
            ).group_by(
                VideoTranslationTaskTag.task_id
            ).having(
                func.count(func.distinct(VideoTranslationTag.normalized_name)) == len(normalized_tags)
            ).subquery()
            query = query.filter(VideoTranslationTask.id.in_(tagged_task_ids))
    
    total = query.count()
    tasks = query.order_by(VideoTranslationTask.created_at.desc()).offset(offset).limit(page_size).all()

    return {
        "items": [
            _serialize_video_translation_task(task)
            for task in tasks
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/tasks/download-selected")
def download_selected_video_translation_tasks(
    request: DownloadSelectedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not request.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请选择要下载的视频")

    task_ids = list(dict.fromkeys(item.task_id for item in request.items))
    tasks = db.query(VideoTranslationTask).filter(
        VideoTranslationTask.id.in_(task_ids),
        VideoTranslationTask.user_id == current_user.id
    ).all()
    task_map = {task.id: task for task in tasks}

    if len(task_map) != len(task_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部分任务不存在")

    archive_buffer = tempfile.SpooledTemporaryFile(max_size=64 * 1024 * 1024)
    used_names = set()
    added_files = 0

    try:
        with zipfile.ZipFile(archive_buffer, mode="w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
            for selected_item in request.items:
                task = task_map.get(selected_item.task_id)
                if not task:
                    continue

                language_results = _get_task_language_results(task)
                result_url = None

                if selected_item.language_code:
                    language_result = language_results.get(selected_item.language_code)
                    if isinstance(language_result, dict):
                        result_url = language_result.get("result_video_url")

                if not result_url:
                    result_url = task.result_video_url

                if not result_url:
                    continue

                zip_filename = _unique_zip_filename(
                    _build_video_translation_download_filename(
                        task,
                        selected_item.language_code,
                        result_url,
                        selected_item.filename
                    ),
                    used_names
                )

                with requests.get(result_url, stream=True, timeout=(10, 300), allow_redirects=True) as response:
                    response.raise_for_status()
                    with archive.open(zip_filename, "w") as archive_entry:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                archive_entry.write(chunk)
                added_files += 1

        if added_files == 0:
            archive_buffer.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="没有可下载的视频")

        archive_buffer.seek(0)
    except HTTPException:
        raise
    except requests.RequestException as e:
        archive_buffer.close()
        logger.error("Download selected video translation failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="下载视频文件失败，请稍后重试")
    except Exception as e:
        archive_buffer.close()
        logger.error("Create selected video translation zip failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="打包下载失败")

    def iter_archive():
        try:
            while True:
                chunk = archive_buffer.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            archive_buffer.close()

    return StreamingResponse(
        iter_archive(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="selected-translations.zip"'}
    )


@router.patch("/tasks/{task_id}")
async def update_video_translation_task_name(
    task_id: int,
    payload: UpdateTaskNameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(VideoTranslationTask).filter(
        VideoTranslationTask.id == task_id,
        VideoTranslationTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.original_filename = payload.original_filename
    db.commit()
    db.refresh(task)
    return _serialize_video_translation_task(task)


@router.post("/tasks/refresh-status")
async def refresh_video_translation_task_statuses(
    task_ids: list[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refresh the status of multiple video translation tasks from Docker service"""
    logger.info(f"Refreshing status for video translation tasks: {task_ids}")
    tasks = db.query(VideoTranslationTask).filter(
        VideoTranslationTask.id.in_(task_ids),
        VideoTranslationTask.user_id == current_user.id
    ).all()
    
    results = []
    for task in tasks:
        logger.info(f"Processing video translation task {task.id}, current status: {task.status.value}, docker_task_id: {task.docker_task_id}")
        if task.status == VideoTranslationStatus.PROCESSING and task.docker_task_id and not task.language_results_json:
            try:
                logger.info(f"Querying Docker for task {task.docker_task_id}")
                docker_response = await video_translation_service.get_task_status(task.docker_task_id)
                logger.info(f"Docker response for task {task.docker_task_id}: {docker_response}")
                
                # Update task status based on Docker response
                new_status = docker_response.get("status", task.status.value)
                task.status = VideoTranslationStatus(new_status)
                
                # Update result fields
                if docker_response.get("result_video_url"):
                    task.result_video_url = docker_response["result_video_url"]
                if docker_response.get("error_message"):
                    task.error_message = docker_response["error_message"]
                
                # If completed, set completed_at
                if task.status == VideoTranslationStatus.COMPLETED:
                    task.completed_at = datetime.utcnow()
                    task.current_stage = "completed"
                
                db.commit()
                db.refresh(task)
                logger.info(f"Updated task {task.id} to status {task.status.value}")
            except Exception as e:
                logger.error(f"Failed to refresh task {task.id}: {str(e)}")
        
        serialized_task = _serialize_video_translation_task(task)
        results.append({
            "id": serialized_task["id"],
            "status": serialized_task["status"],
            "current_stage": serialized_task["current_stage"],
            "target_languages": serialized_task["target_languages"],
            "language_results": serialized_task["language_results"],
            "charged_points": serialized_task["charged_points"],
            "points_refunded": serialized_task["points_refunded"],
            "result_video_url": serialized_task["result_video_url"],
            "tts_timestamps": serialized_task["tts_timestamps"],
            "error_message": serialized_task["error_message"]
        })
    
    return results


@router.post("/fc-callback")
async def fc_callback(
    request: FcCallbackRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """接收 FC/Docker Service 的任务状态回调"""
    # 验证 API Key
    expected_auth = f"Bearer {settings.CALLBACK_API_KEY}"
    if authorization not in (expected_auth, settings.CALLBACK_API_KEY):
        logger.warning(f"Invalid authorization header: {authorization}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    logger.info(f"Received FC callback for task {request.task_id}, status: {request.status}")
    
    # 查找任务
    task = db.query(VideoTranslationTask).filter(VideoTranslationTask.id == request.task_id).first()
    if not task:
        logger.warning(f"Task {request.task_id} not found")
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 更新任务状态
    if request.status == "completed":
        task.status = VideoTranslationStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.current_stage = "completed"
        if request.result_video_url:
            task.result_video_url = request.result_video_url
    elif request.status == "failed":
        task.status = VideoTranslationStatus.FAILED
        task.error_message = request.error_message
        task.current_stage = None
        # 退还积分
        _refund_translation_points(db, task)
    elif request.status == "processing":
        task.status = VideoTranslationStatus.PROCESSING
        task.current_stage = "video_translation"
    
    # 更新语言结果
    if request.language_results:
        task.language_results_json = json.dumps(request.language_results, ensure_ascii=False, default=_json_default)
    
    db.commit()
    logger.info(f"Task {request.task_id} updated to status {request.status}")
    
    return {"status": "success", "task_id": task.id}
