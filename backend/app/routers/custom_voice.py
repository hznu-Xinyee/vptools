import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.custom_voice import CustomVoice
from app.schemas.custom_voice import CustomVoiceCreate, CustomVoiceUpdate, CustomVoiceResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/custom-voices", response_model=CustomVoiceResponse)
def create_custom_voice(
    voice: CustomVoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a custom voice"""
    db_voice = CustomVoice(
        user_id=current_user.id,
        name=voice.name,
        voice_id=voice.voice_id,
        language=voice.language,
        gender=voice.gender,
        description=voice.description
    )
    db.add(db_voice)
    db.commit()
    db.refresh(db_voice)
    return db_voice


@router.get("/custom-voices", response_model=List[CustomVoiceResponse])
def list_custom_voices(
    language: Optional[str] = None,
    gender: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List custom voices with optional filtering"""
    query = db.query(CustomVoice).filter(CustomVoice.user_id == current_user.id, CustomVoice.is_active == True)
    
    if language:
        query = query.filter(CustomVoice.language == language)
    if gender:
        query = query.filter(CustomVoice.gender == gender)
    
    voices = query.order_by(CustomVoice.created_at.desc()).all()
    return voices


@router.get("/custom-voices/{voice_id}", response_model=CustomVoiceResponse)
def get_custom_voice(
    voice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific custom voice"""
    voice = db.query(CustomVoice).filter(
        CustomVoice.id == voice_id,
        CustomVoice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    return voice


@router.put("/custom-voices/{voice_id}", response_model=CustomVoiceResponse)
def update_custom_voice(
    voice_id: int,
    voice_update: CustomVoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a custom voice"""
    voice = db.query(CustomVoice).filter(
        CustomVoice.id == voice_id,
        CustomVoice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    update_data = voice_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(voice, field, value)
    
    db.commit()
    db.refresh(voice)
    return voice


@router.delete("/custom-voices/{voice_id}")
def delete_custom_voice(
    voice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a custom voice (soft delete)"""
    voice = db.query(CustomVoice).filter(
        CustomVoice.id == voice_id,
        CustomVoice.user_id == current_user.id
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    
    voice.is_active = False
    db.commit()
    
    return {"message": "Voice deleted successfully"}
