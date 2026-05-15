from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import asyncio
import logging
import io

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.subtitle_task import SubtitleTask, TaskStatus
from app.schemas.subtitle_task import (
    SubtitleTaskCreate,
    SubtitleTaskResponse,
    SubtitleTaskSubmitRequest,
    SubtitleTaskSubmitResponse
)
from app.services.oss_service import oss_service
from app.services.volcengine_service import volcengine_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload-file", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload file directly to OSS via backend"""
    try:
        # Read file content
        content = await file.read()

        # Generate OSS key
        oss_key = oss_service.generate_upload_key(file.filename, current_user.id)

        # Upload to OSS
        oss_service.upload_file(oss_key, io.BytesIO(content), content_type=file.content_type)

        # Get the file URL
        file_url = oss_service.get_file_url(oss_key)

        return {
            "oss_key": oss_key,
            "file_url": file_url
        }
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")


@router.post("/upload-file-multipart", response_model=dict)
async def upload_file_multipart(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload file to OSS via backend using multipart (10MB chunks)"""
    try:
        import uuid
        upload_id = uuid.uuid4().hex
        oss_key = oss_service.generate_upload_key(file.filename, current_user.id)
        file_url = oss_service.upload_file_multipart(file, oss_key, upload_id)

        return {
            "oss_key": oss_key,
            "file_url": file_url,
            "upload_id": upload_id
        }
    except Exception as e:
        logger.error(f"File multipart upload error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/upload-progress/{upload_id}")
async def get_upload_progress(upload_id: str):
    from app.services.oss_service import upload_progress
    if upload_id not in upload_progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    return upload_progress[upload_id]


@router.post("/upload-url", response_model=dict)
async def get_upload_url(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Generate a presigned URL for uploading video to OSS"""
    oss_key = oss_service.generate_upload_key(filename, current_user.id)
    upload_url = oss_service.generate_presigned_url(oss_key, expires=3600, method='PUT')
    
    return {
        "oss_key": oss_key,
        "upload_url": upload_url,
        "expires_in": 3600
    }


@router.get("/upload-url", response_model=dict)
async def get_upload_url_get(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Generate a presigned URL for uploading video to OSS (GET method for preflight)"""
    oss_key = oss_service.generate_upload_key(filename, current_user.id)
    upload_url = oss_service.generate_presigned_url(oss_key, expires=3600, method='PUT')
    
    return {
        "oss_key": oss_key,
        "upload_url": upload_url,
        "expires_in": 3600
    }


@router.post("/submit", response_model=SubtitleTaskSubmitResponse)
async def submit_subtitle_erase_task(
    task_data: SubtitleTaskSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a subtitle erase task"""
    try:
        # Check and deduct points
        required_points = 5
        if current_user.points < required_points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"积分不足，需要 {required_points} 积分，当前积分: {current_user.points}"
            )
        
        current_user.points -= required_points
        
        # Create task record
        task = SubtitleTask(
            user_id=current_user.id,
            original_filename=task_data.original_filename,
            oss_url=task_data.video_url,
            oss_key=task_data.oss_key,
            status=TaskStatus.PROCESSING
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Generate presigned download URL for VolcEngine (7 days expiration)
        presigned_url = oss_service.generate_download_url(task.oss_key, expires=604800)
        logger.info(f"Generated presigned URL for task {task.id}: {presigned_url[:100]}...")
        
        # Submit to VolcEngine with presigned URL
        volcengine_response = await volcengine_service.submit_subtitle_erase_task(
            presigned_url,
            task_data.mode or "Subtitle"
        )
        
        logger.info(f"VolcEngine submit response: {volcengine_response}")
        
        # Update task with VolcEngine task ID
        task.volcengine_task_id = volcengine_response.get("task_id")
        db.commit()
        db.refresh(task)
        
        return SubtitleTaskSubmitResponse(
            task_id=task.id,
            volcengine_task_id=task.volcengine_task_id,
            status=task.status
        )
    except Exception as e:
        # Rollback on error
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/tasks")
async def get_user_tasks(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all subtitle tasks for the current user with pagination"""
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count
    total = db.query(SubtitleTask).filter(
        SubtitleTask.user_id == current_user.id
    ).count()
    
    # Get tasks
    tasks = db.query(SubtitleTask).filter(
        SubtitleTask.user_id == current_user.id
    ).order_by(SubtitleTask.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Convert to response format
    task_list = [
        {
            "id": task.id,
            "user_id": task.user_id,
            "original_filename": task.original_filename,
            "oss_key": task.oss_key,
            "oss_url": task.oss_url,
            "volcengine_task_id": task.volcengine_task_id,
            "result_video_url": task.result_video_url,
            "result_duration": task.result_duration,
            "status": task.status.value,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
        for task in tasks
    ]
    
    return {
        "items": task_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/tasks/{task_id}", response_model=SubtitleTaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific task by ID"""
    task = db.query(SubtitleTask).filter(
        SubtitleTask.id == task_id,
        SubtitleTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.patch("/tasks/{task_id}")
async def update_task_name(
    task_id: int,
    original_filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the original filename of a task"""
    task = db.query(SubtitleTask).filter(
        SubtitleTask.id == task_id,
        SubtitleTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task.original_filename = original_filename
    db.commit()
    db.refresh(task)
    
    return task


@router.post("/tasks/refresh-status")
async def refresh_task_statuses(
    task_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refresh the status of multiple tasks from VolcEngine"""
    logger.info(f"Refreshing status for tasks: {task_ids}")
    tasks = db.query(SubtitleTask).filter(
        SubtitleTask.id.in_(task_ids),
        SubtitleTask.user_id == current_user.id
    ).all()
    
    results = []
    for task in tasks:
        logger.info(f"Processing task {task.id}, current status: {task.status.value}, volcengine_task_id: {task.volcengine_task_id}")
        if task.status == TaskStatus.PROCESSING and task.volcengine_task_id:
            try:
                logger.info(f"Querying VolcEngine for task {task.volcengine_task_id}")
                volcengine_response = await volcengine_service.get_task_status(
                    task.volcengine_task_id
                )
                logger.info(f"VolcEngine response for task {task.volcengine_task_id}: {volcengine_response}")
                
                # Check VolcEngine status field directly
                volcengine_status = volcengine_response.get("status")
                logger.info(f"VolcEngine status: {volcengine_status}")
                
                if volcengine_status == "success" or volcengine_response.get("success", False) and "result" in volcengine_response:
                    result = volcengine_response.get("result", {})
                    task.result_video_url = result.get("video_url")
                    task.result_duration = result.get("duration")
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
                    logger.info(f"Task {task.id} completed successfully. Result video URL: {task.result_video_url}")
                elif volcengine_status == "failed" or "error" in volcengine_response:
                    task.status = TaskStatus.FAILED
                    error = volcengine_response.get("error", {})
                    task.error_message = error.get("message", "Unknown error")
                    logger.error(f"Task {task.id} failed: {task.error_message}")
                else:
                    logger.info(f"Task {task.id} still processing (status: {volcengine_status})")
                
                db.commit()
                db.refresh(task)
            except Exception as e:
                logger.error(f"Failed to refresh task {task.id}: {str(e)}")
        
        results.append({
            "id": task.id,
            "status": task.status.value,
            "result_video_url": task.result_video_url,
            "error_message": task.error_message
        })
    
    logger.info(f"Refresh results: {results}")
    return results
