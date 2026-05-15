from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import logging
import io
import json
import asyncio

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.subtitle_extract import SubtitleExtractTask, ExtractStatus
from app.models.subtitle_task import SubtitleTask, TaskStatus
from app.models.video_translation import VideoTranslationTask, VideoTranslationStatus
from app.schemas.video_translation import SubtitleParams, VideoTranslationSubmitRequest, VideoTranslationSubmitResponse
from app.services.oss_service import oss_service
from app.services.ice_service import ice_service
from app.services.video_translation_service import video_translation_service
from app.services.ata_service import ata_service
from app.services.volcengine_service import volcengine_service


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


logger = logging.getLogger(__name__)
router = APIRouter()
AUTO_TRANSLATION_MAX_CONCURRENT_TASKS = 3
auto_translation_semaphore = asyncio.Semaphore(AUTO_TRANSLATION_MAX_CONCURRENT_TASKS)


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


def _set_task_language_results(task: VideoTranslationTask, language_results: Dict[str, Any]) -> None:
    task.language_results_json = json.dumps(language_results, ensure_ascii=False, default=_json_default)


def _language_results_for_response(task: VideoTranslationTask) -> Dict[str, Any]:
    results = _get_task_language_results(task)
    if results:
        return results

    if not task.target_language:
        return {}

    result = {
        "status": task.status.value,
        "docker_task_id": task.docker_task_id,
        "result_video_url": task.result_video_url,
        "tts_timestamps": _json_loads(task.tts_timestamps, None),
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
        "language_results": _language_results_for_response(task),
        "tts_timestamps": _json_loads(task.tts_timestamps, None),
        "error_message": task.error_message,
        "is_auto": task.is_auto,
        "current_stage": task.current_stage,
        "charged_points": task.charged_points or 0,
        "points_refunded": bool(task.points_refunded),
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
    skip_subtitle_erasure: bool = False
    subtitle_params: Optional[SubtitleParams] = None


async def process_auto_translation_background(
    task_id: int,
    oss_key: str,
    file_url: str,
    original_filename: str,
    target_languages: List[str],
    skip_subtitle_erasure: bool = False,
    subtitle_params: Optional[Dict[str, Any]] = None
):
    """Background task to process auto translation workflow"""
    logger.info(f"[自动翻译] 任务 {task_id} 已进入后台队列，最多同时处理 {AUTO_TRANSLATION_MAX_CONCURRENT_TASKS} 个任务")
    async with auto_translation_semaphore:
        await _process_auto_translation_background(
            task_id,
            oss_key,
            file_url,
            original_filename,
            target_languages,
            skip_subtitle_erasure,
            subtitle_params
        )


async def _process_auto_translation_background(
    task_id: int,
    oss_key: str,
    file_url: str,
    original_filename: str,
    target_languages: List[str],
    skip_subtitle_erasure: bool = False,
    subtitle_params: Optional[Dict[str, Any]] = None
):
    """Run one auto translation workflow after acquiring queue slot"""
    db = next(get_db())
    try:
        logger.info(f"[自动翻译] 任务 {task_id} 已获得处理槽位，开始执行")
        logger.info(f"[自动翻译] 开始自动翻译工作流，任务ID: {task_id}")
        logger.info(f"[自动翻译] 文件: {original_filename}, 目标语言: {', '.join(target_languages)}")
        
        # Step 1: Audio Separation and Subtitle Extraction
        logger.info(f"[自动翻译] 步骤 1/3: 开始声伴分离与字幕提取，任务ID: {task_id}")
        task = db.query(VideoTranslationTask).filter(VideoTranslationTask.id == task_id).first()
        if task:
            task.current_stage = "subtitle_extraction"
            db.commit()
            logger.info(f"[自动翻译] 更新任务 {task_id} 的当前阶段为字幕提取")

        logger.info(f"[自动翻译] 为 {original_filename} 创建字幕提取任务")
        extract_task = SubtitleExtractTask(
            user_id=task.user_id,
            source_oss_key=oss_key,
            original_filename=original_filename,
            source_type="video",
            status=ExtractStatus.PROCESSING
        )
        db.add(extract_task)
        db.commit()
        db.refresh(extract_task)
        logger.info(f"[自动翻译] 创建字幕提取任务 {extract_task.id}")

        logger.info(f"[自动翻译] 从 {file_url} 下载视频")
        import requests
        video_response = requests.get(file_url, timeout=30)
        video_response.raise_for_status()
        video_data = video_response.content
        logger.info(f"[自动翻译] 视频下载完成，大小: {len(video_data)} 字节")

        voice_audio_url = None
        original_audio_url = None
        background_audio_url = None
        logger.info(f"[自动翻译] 步骤 1.1/3: 开始音频分离（声伴分离）")
        import os
        import subprocess
        import tempfile
        temp_video_path = None
        temp_audio_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                temp_video.write(video_data)
                temp_video_path = temp_video.name

            logger.info(f"[自动翻译] 视频已保存到临时文件: {temp_video_path}")

            temp_audio_path = temp_video_path.replace(".mp4", ".wav")
            logger.info(f"[自动翻译] 使用ffmpeg提取原始音频")
            subprocess.run([
                "ffmpeg", "-i", temp_video_path,
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                temp_audio_path, "-y"
            ], check=True, capture_output=True)
            logger.info(f"[自动翻译] 原始音频提取完成: {temp_audio_path}")

            audio_oss_key = f"audio_extraction/{task_id}_original.wav"
            with open(temp_audio_path, 'rb') as audio_file:
                oss_service.upload_file(audio_oss_key, audio_file, content_type="audio/wav")

            original_audio_url = oss_service.generate_presigned_url(audio_oss_key, expires=3600, method='GET')
            extract_task.audio_oss_key = audio_oss_key
            extract_task.audio_oss_url = original_audio_url
            db.commit()
            logger.info(f"[自动翻译] 原始音频已上传到OSS，预签名URL: {original_audio_url}")

            from app.services.mediakit_service import mediakit_service
            logger.info(f"[自动翻译] 提交音频分离任务到MediaKit")
            demix_job_id = await mediakit_service.submit_separate_voice_task(audio_url=original_audio_url)

            if not demix_job_id:
                raise Exception("音频分离任务提交失败")

            logger.info(f"[自动翻译] 音频分离任务已提交，任务ID: {demix_job_id}")

            demix_max_attempts = 60
            logger.info(f"[自动翻译] 等待音频分离完成（最多 {demix_max_attempts} 次尝试）")
            for attempt in range(demix_max_attempts):
                await asyncio.sleep(10)
                demix_status = await mediakit_service.get_task_status(demix_job_id)
                status = demix_status.get('status') if demix_status else 'None'
                logger.info(f"[自动翻译] 音频分离状态检查 {attempt + 1}/{demix_max_attempts}: {status}")

                if mediakit_service.is_task_completed(demix_status):
                    logger.info(f"[自动翻译] 音频分离成功完成")
                    result = demix_status.get("result", {})
                    voice_audio_url = result.get("voice_audio_url") or result.get("vocal_audio_url")
                    background_audio_url = result.get("background_audio_url")
                    if background_audio_url:
                        task.background_audio_url = background_audio_url
                        db.commit()
                        logger.info(f"[自动翻译] 背景音URL已保存到数据库: {background_audio_url}")
                    if voice_audio_url:
                        logger.info(f"[自动翻译] 人声音频URL将用于ATA字幕识别: {voice_audio_url}")
                    else:
                        logger.warning(f"[自动翻译] 音频分离完成但未返回人声音频URL，将使用原始音频提交ATA")
                    break
                elif mediakit_service.is_task_failed(demix_status):
                    raise Exception(f"音频分离任务失败: {demix_status}")
                elif attempt >= demix_max_attempts - 1:
                    raise Exception("音频分离超时")

        except Exception as e:
            logger.error(f"[自动翻译] 音频分离失败: {str(e)}")
            logger.warning(f"[自动翻译] 将使用原始音频提交ATA，并继续使用原视频音频")
        finally:
            logger.info(f"[自动翻译] 清理临时文件")
            for temp_path in (temp_video_path, temp_audio_path):
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)

        # Submit to ATA after audio separation
        ata_audio_url = voice_audio_url or original_audio_url
        if ata_audio_url:
            logger.info(f"[自动翻译] 使用音频URL提交到ATA进行字幕提取: {ata_audio_url}")
            ata_task_id = await ata_service.submit_audio(ata_audio_url)
        else:
            logger.warning(f"[自动翻译] 没有可用音频URL，将回退使用原视频数据提交ATA")
            ata_task_id = await ata_service.submit_audio_binary(video_data)
        extract_task.ata_task_id = ata_task_id
        db.commit()
        logger.info(f"[自动翻译] 已提交到ATA，任务ID: {ata_task_id}")

        # Wait for completion
        max_attempts = 60
        logger.info(f"[自动翻译] 等待字幕提取完成（最多 {max_attempts} 次尝试）")
        for attempt in range(max_attempts):
            await asyncio.sleep(10)
            try:
                ata_status = await ata_service.get_task_status(ata_task_id)
                logger.info(f"[自动翻译] ATA状态检查 {attempt + 1}/{max_attempts}: {ata_status.get('code')}")
                if ata_service.is_task_completed(ata_status):
                    extract_task.status = ExtractStatus.COMPLETED
                    extract_task.subtitle_result = json.dumps({"utterances": ata_status.get("utterances", [])}, ensure_ascii=False)
                    db.commit()
                    logger.info(f"[自动翻译] 字幕提取成功完成")
                    break
                elif ata_service.is_task_failed(ata_status):
                    extract_task.status = ExtractStatus.FAILED
                    extract_task.error_message = str(ata_status)
                    db.commit()
                    logger.error(f"[自动翻译] 字幕提取失败: {extract_task.error_message}")
                    raise Exception(f"字幕提取失败: {extract_task.error_message}")
            except Exception as e:
                logger.warning(f"[自动翻译] ATA状态检查第 {attempt + 1} 次失败: {str(e)}")
                if attempt >= max_attempts - 1:
                    raise
                await asyncio.sleep(10)

        erasure_video_url = None
        if skip_subtitle_erasure:
            logger.info(f"[自动翻译] 步骤 2/3: 已开启跳过字幕擦除，任务ID: {task_id}")
        else:
            # Step 2: Subtitle Erasure
            logger.info(f"[自动翻译] 步骤 2/3: 执行字幕擦除，任务ID: {task_id}")
            task = db.query(VideoTranslationTask).filter(VideoTranslationTask.id == task_id).first()
            if task:
                task.current_stage = "subtitle_erasure"
                db.commit()
                logger.info(f"[自动翻译] 更新任务 {task_id} 的当前阶段为字幕擦除")

            # Submit subtitle erasure task
            presigned_url = oss_service.generate_download_url(oss_key, expires=604800)
            logger.info(f"[自动翻译] 生成预签名URL用于字幕擦除: {presigned_url[:100]}...")
            
            volcengine_response = await volcengine_service.submit_subtitle_erase_task(
                presigned_url,
                "Subtitle"
            )
            logger.info(f"[自动翻译] 字幕擦除任务已提交，响应: {volcengine_response}")
            
            # Wait for subtitle erasure completion
            erasure_volcengine_task_id = volcengine_response.get("task_id")
            erasure_max_attempts = 600
            logger.info(f"[自动翻译] 等待字幕擦除完成（最多 {erasure_max_attempts} 次尝试）")
            
            for attempt in range(erasure_max_attempts):
                await asyncio.sleep(10)
                try:
                    erasure_status = await volcengine_service.get_task_status(erasure_volcengine_task_id)
                    logger.info(f"[自动翻译] 字幕擦除状态检查 {attempt + 1}/{erasure_max_attempts}: {erasure_status.get('status')}")
                    
                    if erasure_status.get("status") == "success" or (erasure_status.get("success", False) and "result" in erasure_status):
                        result = erasure_status.get("result", {})
                        erasure_video_url = result.get("video_url")
                        logger.info(f"[自动翻译] 字幕擦除成功完成，结果视频URL: {erasure_video_url}")
                        break
                    elif erasure_status.get("status") == "failed" or "error" in erasure_status:
                        logger.warning(f"[自动翻译] 字幕擦除失败，将使用原视频继续")
                        erasure_video_url = file_url
                        break
                except Exception as e:
                    logger.warning(f"[自动翻译] 字幕擦除状态检查第 {attempt + 1} 次失败: {str(e)}")
                    if attempt >= erasure_max_attempts - 1:
                        logger.warning(f"[自动翻译] 字幕擦除超时，将使用原视频继续")
                        erasure_video_url = file_url
        
        # Use erasure video if available, otherwise use original video
        final_video_url = erasure_video_url or file_url
        logger.info(f"[自动翻译] 将使用视频进行翻译: {final_video_url}")

        final_video_ice_url = final_video_url
        if erasure_video_url:
            logger.info(f"[自动翻译] 下载字幕擦除结果并上传到OSS用于ICE注册")
            erasure_response = requests.get(erasure_video_url, timeout=300)
            erasure_response.raise_for_status()
            erasure_video_oss_key = f"auto_translate_erased/{task_id}_{original_filename}"
            oss_service.upload_file(
                erasure_video_oss_key,
                io.BytesIO(erasure_response.content),
                content_type="video/mp4"
            )
            final_video_ice_url = f"oss://{settings.OSS_BUCKET_NAME}/{erasure_video_oss_key}"
            logger.info(f"[自动翻译] 字幕擦除结果已上传到OSS用于ICE注册: {final_video_ice_url}")
        elif oss_key:
            final_video_ice_url = f"oss://{settings.OSS_BUCKET_NAME}/{oss_key}"
            logger.info(f"[自动翻译] 使用原视频OSS地址注册ICE: {final_video_ice_url}")

        # Get subtitles
        logger.info(f"[自动翻译] 从提取任务 {extract_task.id} 获取字幕数据")
        if not extract_task.subtitle_result:
            logger.error(f"[自动翻译] 提取任务 {extract_task.id} 中未找到字幕结果")
            raise Exception("字幕提取失败，无法获取字幕数据")

        subtitle_data = json.loads(extract_task.subtitle_result).get("utterances", [])
        logger.info(f"[自动翻译] 获取到 {len(subtitle_data)} 条字幕")

        # Register video with ICE
        logger.info(f"[自动翻译] 在ICE中注册视频: {final_video_ice_url}")
        media_id = ice_service.register_media(final_video_ice_url, oss_key, "video")
        logger.info(f"[自动翻译] 视频已在ICE中注册，媒体ID: {media_id}")

        # Register background audio to ICE if available
        background_audio_media_id = None
        current_background_audio_url = background_audio_url or task.background_audio_url
        logger.info(f"[自动翻译] 准备注册背景音，URL: {current_background_audio_url}")
        if current_background_audio_url:
            try:
                logger.info(f"[自动翻译] 在ICE中注册背景音: {current_background_audio_url}")
                # Download background audio and upload to OSS for ICE registration
                logger.info(f"[自动翻译] 下载背景音")
                async with httpx.AsyncClient(timeout=300.0) as client:
                    background_audio_response = await client.get(current_background_audio_url)
                    background_audio_response.raise_for_status()
                    background_audio_data = background_audio_response.content
                
                # Upload background audio to OSS
                logger.info(f"[自动翻译] 上传背景音到OSS")
                background_audio_oss_key = f"audio_separation/{task_id}_background.aac"
                oss_service.upload_file(background_audio_oss_key, background_audio_data)
                background_oss_url = f"oss://{settings.OSS_BUCKET_NAME}/{background_audio_oss_key}"
                logger.info(f"[自动翻译] 背景音已上传到OSS: {background_oss_url}")
                
                background_audio_media_id = ice_service.register_media(
                    background_oss_url,
                    background_audio_oss_key,
                    "audio"
                )
                logger.info(f"[自动翻译] 背景音已在ICE中注册，媒体ID: {background_audio_media_id}")
                if not background_audio_media_id:
                    logger.warning(f"[自动翻译] 背景音ICE注册返回空media_id")
            except Exception as e:
                logger.warning(f"[自动翻译] 背景音注册失败: {str(e)}，将使用原视频音频")
        
        # Submit video translation
        logger.info(f"[自动翻译] 提交视频翻译到Docker服务")
        default_subtitle_params = {
            "alignment": "TopCenter",
            "font_size": 84,
            "font_color": "#ffffff",
            "font": "Alibaba PuHuiTi",
            "outline": 2,
            "outline_colour": "#000000",
            "y": 0.75
        }
        subtitle_params_for_render = {
            **default_subtitle_params,
            **{key: value for key, value in (subtitle_params or {}).items() if value is not None}
        }

        language_results = _get_task_language_results(task)
        first_language = target_languages[0]
        failed_language = None
        has_pending_language = False
        for target_language in target_languages:
            logger.info(f"[自动翻译] 提交 {target_language} 视频翻译到Docker服务")
            language_results[target_language] = {
                **language_results.get(target_language, {}),
                "status": "processing",
            }
            _set_task_language_results(task, language_results)
            db.commit()

            try:
                docker_response = await video_translation_service.submit_task(
                    media_id=media_id,
                    subtitle_json=subtitle_data,
                    target_language=target_language,
                    task_id=task_id,
                    subtitle_params=subtitle_params_for_render,
                    background_audio_media_id=background_audio_media_id,
                    background_audio_url=current_background_audio_url
                )
                logger.info(f"[自动翻译] {target_language} Docker服务响应: {docker_response}")
            except Exception as exc:
                docker_response = {"status": "failed", "error_message": str(exc)}

            result_status = docker_response.get("status", "processing")
            language_results[target_language] = {
                "status": result_status,
                "docker_task_id": docker_response.get("docker_task_id") or docker_response.get("task_id"),
                "result_video_url": docker_response.get("result_video_url"),
                "timeline_json": docker_response.get("timeline_json"),
                "tts_timestamps": docker_response.get("tts_timestamps"),
                "error_message": docker_response.get("error_message"),
            }
            _set_task_language_results(task, language_results)

            if target_language == first_language:
                task.docker_task_id = language_results[target_language]["docker_task_id"]
                task.timeline_json = json.dumps(docker_response.get("timeline_json"), ensure_ascii=False) if docker_response.get("timeline_json") else None
                task.tts_timestamps = json.dumps(docker_response.get("tts_timestamps"), ensure_ascii=False) if docker_response.get("tts_timestamps") else None
                task.result_video_url = docker_response.get("result_video_url")

            db.commit()

            if result_status == "failed":
                failed_language = target_language
                task.error_message = docker_response.get("error_message", f"{target_language} 视频翻译失败")
                break
            if result_status != "completed":
                has_pending_language = True

        if failed_language:
            task.status = VideoTranslationStatus.FAILED
            task.current_stage = None
            _refund_translation_points(db, task)
            db.commit()
            logger.error(f"[自动翻译] 任务 {task_id} 的 {failed_language} 视频翻译失败: {task.error_message}")
        else:
            if has_pending_language:
                task.status = VideoTranslationStatus.PROCESSING
                task.current_stage = "video_translation"
                logger.info(f"[自动翻译] 任务 {task_id} 的视频翻译已提交，等待渲染完成")
            else:
                task.status = VideoTranslationStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                task.current_stage = "completed"
                logger.info(f"[自动翻译] 任务 {task_id} 的视频翻译全部完成")
            db.commit()
        
        db.commit()
        logger.info(f"[自动翻译] 自动翻译任务 {task_id} 的工作流已完成")
        
    except Exception as e:
        logger.error(f"[自动翻译] 自动翻译后台任务失败，任务ID: {task_id}，错误: {str(e)}", exc_info=True)
        try:
            task = db.query(VideoTranslationTask).filter(VideoTranslationTask.id == task_id).first()
            if task:
                task.status = VideoTranslationStatus.FAILED
                task.error_message = str(e)
                task.current_stage = None
                _refund_translation_points(db, task)
                db.commit()
                logger.error(f"[自动翻译] 已将任务 {task_id} 标记为失败")
        except Exception as db_error:
            logger.error(f"[自动翻译] 更新任务状态失败: {str(db_error)}")
            db.rollback()
    finally:
        try:
            db.close()
        except:
            pass
        logger.info(f"[自动翻译] 任务 {task_id} 的数据库连接已关闭")


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
        db.commit()
        db.refresh(task)
        
        subtitle_params = _model_dump_exclude_none(request.subtitle_params) if request.subtitle_params else None

        # Start background processing
        asyncio.create_task(process_auto_translation_background(
            task.id,
            request.oss_key,
            request.file_url,
            request.original_filename,
            target_languages,
            request.skip_subtitle_erasure,
            subtitle_params
        ))

        return {
            "task_id": task.id,
            "status": task.status.value,
            "target_languages": target_languages,
            "charged_points": required_points,
            "message": "任务已提交，正在排队处理"
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


@router.get("/tasks")
async def get_video_translation_tasks(
    page: int = 1,
    page_size: int = 10,
    is_auto: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    offset = (page - 1) * page_size
    query = db.query(VideoTranslationTask).filter(VideoTranslationTask.user_id == current_user.id)
    
    if is_auto is not None:
        query = query.filter(VideoTranslationTask.is_auto == is_auto)
    
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
