import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from elevenlabs.client import ElevenLabs

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.custom_voice import CustomVoice
from app.schemas.custom_voice import CustomVoiceCreate, CustomVoiceUpdate, CustomVoiceResponse

logger = logging.getLogger(__name__)
router = APIRouter()

ELEVENLABS_API_KEY = "sk_f6cabc1d61c9cbf3f8591e87afd5a2ce2bf281a38f880559"
HELLO_VOICES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "public", "hello_voices")


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
    """List all custom voices (shared across all users) with optional filtering"""
    query = db.query(CustomVoice).filter(CustomVoice.is_active == True)

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


@router.post("/generate-voice-preview")
def generate_voice_preview(
    voice_id: str,
    language: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a preview audio for a voice"""
    # Greeting text mapping
    greetings = {
        "tl": "Kamusta",
        "fil": "Kamusta",
        "vi": "Xin chào",
        "en": "Hello",
        "id": "Halo",
        "ms": "Helo",
        "th": "สวัสดี"
    }

    text = greetings.get(language, "Hello")
    output_path = os.path.join(HELLO_VOICES_DIR, f"{voice_id}.mp3")

    # Check if preview already exists
    if os.path.exists(output_path):
        return FileResponse(output_path, media_type="audio/mpeg")

    # Generate new preview
    try:
        os.makedirs(HELLO_VOICES_DIR, exist_ok=True)

        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",
        )

        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        return FileResponse(output_path, media_type="audio/mpeg")

    except Exception as e:
        logger.error(f"Failed to generate voice preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")
