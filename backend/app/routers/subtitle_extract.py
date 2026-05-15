from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging
import os
import tempfile

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.subtitle_extract import SubtitleExtractTask, ExtractStatus
from app.schemas.subtitle_extract import (
    SubtitleExtractCreate,
    SubtitleExtractResponse,
    SubtitleExtractSubmitRequest,
    SubtitleExtractSubmitResponse
)
from app.services.oss_service import oss_service
from app.services.audio_conversion import audio_conversion_service
from app.services.ata_service import ata_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload-file")
async def upload_extract_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload file for subtitle extraction"""
    try:
        # Generate OSS key
        oss_key = oss_service.generate_upload_key(file.filename, current_user.id)

        # Upload file to OSS
        oss_service.upload_file(oss_key, file.file, file.content_type)

        # Get file URL
        file_url = oss_service.get_file_url(oss_key)

        return {
            "oss_key": oss_key,
            "file_url": file_url
        }
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/upload-file-multipart")
async def upload_extract_file_multipart(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload file for subtitle extraction using multipart (10MB chunks)"""
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
        logger.error(f"File multipart upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/upload-progress/{upload_id}")
async def get_upload_progress(upload_id: str):
    from app.services.oss_service import upload_progress
    if upload_id not in upload_progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    return upload_progress[upload_id]


@router.post("/submit", response_model=SubtitleExtractSubmitResponse)
async def submit_subtitle_extract_task(
    task_data: SubtitleExtractSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a subtitle extraction task"""
    try:
        # Create task record
        task = SubtitleExtractTask(
            user_id=current_user.id,
            original_filename=task_data.original_filename,
            source_type=task_data.source_type,
            source_oss_key=task_data.oss_key,
            status=ExtractStatus.PROCESSING
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Convert to audio
        if task_data.source_type == "history_video":
            # Get the original video from subtitle erase history
            from app.models.subtitle_task import SubtitleTask
            history_task = db.query(SubtitleTask).filter(
                SubtitleTask.id == task_data.history_task_id,
                SubtitleTask.user_id == current_user.id
            ).first()
            
            if not history_task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="History task not found"
                )
            
            # Convert OSS file to audio binary
            audio_data = await audio_conversion_service.convert_oss_file_to_audio(
                history_task.oss_key
            )
        else:
            # Convert uploaded file to audio binary
            from app.services.oss_service import oss_service
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                oss_service.bucket.get_object_to_file(task_data.oss_key, temp_file.name)
                with open(temp_file.name, 'rb') as f:
                    audio_data = await audio_conversion_service.convert_to_audio(
                        f,
                        task_data.original_filename
                    )
                os.unlink(temp_file.name)
        
        # Submit to ATA using binary upload
        ata_task_id = await ata_service.submit_audio_binary(audio_data)
        task.ata_task_id = ata_task_id
        
        db.commit()
        db.refresh(task)
        
        logger.info(f"ATA task submitted: {ata_task_id}")
        
        return SubtitleExtractSubmitResponse(
            task_id=task.id,
            ata_task_id=task.ata_task_id,
            status=task.status
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Submit task failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/tasks")
async def get_user_extract_tasks(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all subtitle extraction tasks for the current user with pagination"""
    offset = (page - 1) * page_size
    
    total = db.query(SubtitleExtractTask).filter(
        SubtitleExtractTask.user_id == current_user.id
    ).count()
    
    tasks = db.query(SubtitleExtractTask).filter(
        SubtitleExtractTask.user_id == current_user.id
    ).order_by(SubtitleExtractTask.created_at.desc()).offset(offset).limit(page_size).all()
    
    task_list = [
        {
            "id": task.id,
            "user_id": task.user_id,
            "original_filename": task.original_filename,
            "source_type": task.source_type,
            "audio_oss_url": task.audio_oss_url,
            "ata_task_id": task.ata_task_id,
            "status": task.status.value,
            "subtitle_result": task.subtitle_result,
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


@router.post("/tasks/refresh-status")
async def refresh_extract_task_statuses(
    task_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refresh the status of multiple subtitle extraction tasks from ATA"""
    logger.info(f"Refreshing status for extract tasks: {task_ids}")
    tasks = db.query(SubtitleExtractTask).filter(
        SubtitleExtractTask.id.in_(task_ids),
        SubtitleExtractTask.user_id == current_user.id
    ).all()
    
    results = []
    for task in tasks:
        logger.info(f"Processing extract task {task.id}, current status: {task.status.value}, ata_task_id: {task.ata_task_id}")
        if task.status == ExtractStatus.PROCESSING and task.ata_task_id:
            try:
                logger.info(f"Querying ATA for task {task.ata_task_id}")
                ata_response = await ata_service.get_task_status(task.ata_task_id)
                logger.info(f"ATA response for task {task.ata_task_id}: {ata_response}")
                
                code = ata_response.get("code")
                logger.info(f"ATA status code: {code}")
                
                if code == 0 and "utterances" in ata_response:
                    # Task completed successfully
                    import json
                    # Remove words field from utterances to keep only sentence-level timestamps
                    if "utterances" in ata_response:
                        for utterance in ata_response["utterances"]:
                            utterance.pop("words", None)
                    task.subtitle_result = json.dumps(ata_response, ensure_ascii=False)
                    task.status = ExtractStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
                    logger.info(f"Task {task.id} completed successfully")
                elif code is not None and code != 0 and code != 2000:
                    # Task failed
                    task.status = ExtractStatus.FAILED
                    task.error_message = f"ATA error code: {code}, message: {ata_response.get('message')}"
                    logger.error(f"Task {task.id} failed: {task.error_message}")
                else:
                    logger.info(f"Task {task.id} still processing (code: {code})")
                
                db.commit()
                db.refresh(task)
            except Exception as e:
                logger.error(f"Failed to refresh task {task.id}: {str(e)}")
        
        results.append({
            "id": task.id,
            "status": task.status.value,
            "subtitle_result": task.subtitle_result,
            "error_message": task.error_message
        })
    
    logger.info(f"Refresh results: {results}")
    return results
