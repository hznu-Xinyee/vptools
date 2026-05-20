import uuid
import logging
import json
import httpx
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.schemas import TranslateVideoRequest, TranslateVideoResponse, AutoTranslationRequest, AutoTranslationResponse
from app.translation_service import translation_service
from app.tts_service import tts_service
from app.oss_service import oss_service
from app.timeline_service import timeline_service
from app.ice_service import ice_service
from app.auto_translation_service import auto_translation_service
from app.elevenlabs_service import elevenlabs_service
from app.continuous_dubbing_service import continuous_dubbing_service

app = FastAPI(title="VP Video Translation Docker Service", version="0.1.0")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("video_translation_fc")




async def _ensure_background_audio_media_id(request):
    if request.background_audio_media_id:
        logger.info("background audio media id provided: %s", request.background_audio_media_id)
        return request.background_audio_media_id
    if not request.background_audio_url:
        logger.info("no background audio url provided")
        return None
    logger.info("registering background audio from url in docker-service")
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.get(request.background_audio_url)
        response.raise_for_status()
        audio_data = response.content
    audio_key = oss_service.upload_audio(audio_data, content_type="audio/aac")
    audio_url = oss_service.get_file_url(audio_key)
    media_id = ice_service.register_media(
        input_url=audio_url,
        title=audio_key,
        media_type="audio",
    )
    logger.info("background audio registered in docker-service media_id=%s oss_key=%s", media_id, audio_key)
    return media_id


def _subtitle_to_dict(subtitle):
    if hasattr(subtitle, "model_dump"):
        return subtitle.model_dump()
    if isinstance(subtitle, dict):
        return subtitle
    return {
        "start_time": getattr(subtitle, "start_time", None),
        "end_time": getattr(subtitle, "end_time", None),
        "text": getattr(subtitle, "text", ""),
        "words": getattr(subtitle, "words", None),
    }


def _write_translation_summary(
    docker_task_id,
    request,
    original_subtitles,
    translated_subtitles,
    audio_segments,
    timeline_json,
    result_video_url,
    background_audio_media_id,
):
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    summary_path = logs_dir / f"translation_summary_{request.task_id}_{docker_task_id}.txt"
    payload = {
        "task_id": request.task_id,
        "docker_task_id": docker_task_id,
        "media_id": request.media_id,
        "target_language": request.target_language,
        "result_video_url": result_video_url,
        "background_audio_media_id": background_audio_media_id,
        "original_subtitles": original_subtitles,
        "translated_subtitles": translated_subtitles,
        "audio_segments": audio_segments,
        "timeline_json": timeline_json,
    }
    lines = [
        f"task_id: {request.task_id}",
        f"docker_task_id: {docker_task_id}",
        f"media_id: {request.media_id}",
        f"target_language: {request.target_language}",
        f"result_video_url: {result_video_url}",
        f"background_audio_media_id: {background_audio_media_id}",
        "",
        "# Subtitle / Translation / TTS Details",
    ]
    for index, original in enumerate(original_subtitles):
        translated = translated_subtitles[index] if index < len(translated_subtitles) else {}
        segment = audio_segments[index] if index < len(audio_segments) else {}
        lines.extend([
            "",
            f"## Segment {index}",
            f"original_time_ms: {original.get('start_time')} -> {original.get('end_time')}",
            f"original_text: {original.get('text', '')}",
            f"translated_time_ms: {translated.get('start_time')} -> {translated.get('end_time')}",
            f"translated_text: {translated.get('text', '')}",
            f"audio_media_id: {segment.get('audio_media_id')}",
            f"audio_duration: {segment.get('audio_duration')}",
            f"audio_speed: {segment.get('audio_speed')}",
            "original_words: " + json.dumps(original.get("words") or [], ensure_ascii=False),
            "tts_timestamps: " + json.dumps(segment.get("tts_timestamps") or [], ensure_ascii=False),
        ])
    lines.extend([
        "",
        "# Raw JSON",
        json.dumps(payload, ensure_ascii=False, indent=2),
    ])
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("translation summary saved path=%s", summary_path)
    return str(summary_path)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


class GenerateVoicePreviewRequest(BaseModel):
    voice_id: str
    language: str


@app.post("/generate-voice-preview")
async def generate_voice_preview(request: GenerateVoicePreviewRequest):
    """Generate a preview audio file for a custom voice"""
    try:
        # 创建 hello_voices 目录
        hello_voices_dir = Path("/Users/montageai/Desktop/vp_dev/vptools/video-translation-docker-service/hello_voices")
        hello_voices_dir.mkdir(exist_ok=True)

        # 根据语言选择问候语
        greetings = {
            'zh': '你好',
            'en': 'Hello',
            'ja': 'こんにちは',
            'ko': '안녕하세요',
            'es': 'Hola',
            'fr': 'Bonjour',
            'de': 'Hallo',
            'it': 'Ciao',
            'pt': 'Olá',
            'ru': 'Привет',
            'ar': 'مرحبا',
            'hi': 'नमस्ते',
            'th': 'สวัสดี',
            'vi': 'Xin chào',
            'id': 'Halo',
            'tr': 'Merhaba',
            'pl': 'Cześć',
            'nl': 'Hallo',
            'sv': 'Hej',
        }

        greeting_text = greetings.get(request.language, 'Hello')

        # 使用 ElevenLabs 生成音频
        logger.info(f"Generating voice preview for voice_id={request.voice_id}, language={request.language}, text={greeting_text}")
        audio_data = await elevenlabs_service.synthesize(greeting_text, request.voice_id)

        # 保存音频文件
        audio_filename = f"{request.voice_id}.mp3"
        audio_path = hello_voices_dir / audio_filename
        audio_path.write_bytes(audio_data)

        logger.info(f"Voice preview saved to {audio_path}")

        return {
            "status": "success",
            "audio_url": f"/hello-voices/{audio_filename}",
            "voice_id": request.voice_id
        }
    except Exception as e:
        logger.exception(f"Failed to generate voice preview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hello-voices/{filename}")
async def serve_hello_voice(filename: str):
    """Serve hello voice audio files"""
    file_path = Path("/Users/montageai/Desktop/vp_dev/vptools/video-translation-docker-service/hello_voices") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg")


@app.post("/auto-translation", response_model=AutoTranslationResponse)
async def submit_auto_translation(
    request: AutoTranslationRequest
):
    """Submit auto translation task for FC async invocation"""
    try:
        # Normalize target languages
        raw_languages = request.target_languages if request.target_languages is not None else ([request.target_language] if request.target_language else [])
        target_languages = []
        seen = set()
        for language in raw_languages:
            normalized = str(language).strip() if language is not None else ""
            if normalized and normalized not in seen:
                target_languages.append(normalized)
                seen.add(normalized)

        if not target_languages:
            raise HTTPException(status_code=400, detail="请至少选择一种目标语言")

        result = await auto_translation_service.process_auto_translation(
            request.task_id,
            request.oss_key,
            request.file_url,
            request.original_filename,
            target_languages,
            request.skip_subtitle_erasure,
            request.subtitle_params.model_dump() if request.subtitle_params else None,
            request.custom_voice_id,
            request.custom_voice_map,
            request.continuous_dubbing
        )

        return AutoTranslationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("submit_auto_translation failed task_id=%s", request.task_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate-video", response_model=TranslateVideoResponse)
async def translate_video(request: TranslateVideoRequest):
    try:
        docker_task_id = uuid.uuid4().hex
        audio_segments = []
        try:
            tts_voice_spec, tts_canonical_lang = tts_service.resolve_voice(request.target_language)
        except ValueError as exc:
            logger.warning("translate_video unsupported target_language=%s: %s", request.target_language, exc)
            raise HTTPException(status_code=400, detail=str(exc))
        logger.info(
            "translate_video start task_id=%s docker_task_id=%s media_id=%s target_language=%s tts_voice=%s tts_lang=%s subtitle_count=%s",
            request.task_id,
            docker_task_id,
            request.media_id,
            request.target_language,
            tts_voice_spec.voice,
            tts_canonical_lang,
            len(request.subtitle_json),
        )

        original_subtitles = [_subtitle_to_dict(subtitle) for subtitle in request.subtitle_json]
        background_audio_media_id = await _ensure_background_audio_media_id(request)

        # Step 1: Translate subtitles with optimized timestamps
        logger.info("Starting timestamped translation for %s subtitles", len(request.subtitle_json))
        translated_subtitles = await translation_service.translate_subtitles_with_timestamps(
            request.subtitle_json,
            request.target_language
        )
        logger.info("Timestamped translation completed, got %s subtitles", len(translated_subtitles))

        # Step 2: First round TTS synthesis
        audio_data_list = []
        audio_duration_list = []  # Store audio durations
        unqualified_indices = []  # Indices where TTS duration > original subtitle duration

        for index, translated_subtitle in enumerate(translated_subtitles):
            translated_text = translated_subtitle["text"]
            current_start_time = translated_subtitle["start_time"]
            current_end_time = translated_subtitle["end_time"]
            original_duration = max(0.1, (current_end_time - current_start_time) / 1000)
            logger.info(
                "subtitle[%s] tts start translated=%s start=%s end=%s original_duration=%s",
                index,
                translated_text,
                current_start_time,
                current_end_time,
                original_duration
            )
            tts_result = await tts_service.synthesize_with_timestamps(
                translated_text,
                request.target_language
            )
            audio_data = tts_result.audio_data
            translated_subtitle["tts_timestamps"] = tts_result.timestamps
            logger.info(
                "subtitle[%s] tts audio_size=%s timestamp_count=%s",
                index,
                len(audio_data),
                len(tts_result.timestamps)
            )

            audio_duration = tts_service.get_audio_duration(audio_data)
            logger.info("subtitle[%s] audio_duration=%s seconds", index, audio_duration)
            audio_duration_list.append(audio_duration)

            # Check if TTS duration exceeds original subtitle duration
            if audio_duration > original_duration:
                unqualified_indices.append(index)
                logger.warning(
                    "subtitle[%s] audio_duration=%s > original_duration=%s, marked for re-translation",
                    index,
                    audio_duration,
                    original_duration
                )

            audio_data_list.append(audio_data)

        # Step 3: Re-translate and re-synthesize unqualified subtitles (only once)
        if unqualified_indices:
            logger.info("Found %s unqualified subtitles, re-translating with shortened text", len(unqualified_indices))
            unqualified_original_texts = [request.subtitle_json[i].text for i in unqualified_indices]
            shortened_translations = await translation_service.translate_batch_shorten(
                unqualified_original_texts,
                request.target_language
            )
            logger.info("Re-translation completed, got %s shortened translations", len(shortened_translations))

            # Re-synthesize audio for shortened translations
            for i, idx in enumerate(unqualified_indices):
                translated_text = shortened_translations[i]
                current_start_time = translated_subtitles[idx]["start_time"]
                current_end_time = translated_subtitles[idx]["end_time"]
                original_duration = max(0.1, (current_end_time - current_start_time) / 1000)
                logger.info(
                    "subtitle[%s] re-tts start translated=%s original_duration=%s",
                    idx,
                    translated_text,
                    original_duration
                )
                tts_result = await tts_service.synthesize_with_timestamps(
                    translated_text,
                    request.target_language
                )
                audio_data = tts_result.audio_data
                logger.info(
                    "subtitle[%s] re-tts audio_size=%s timestamp_count=%s",
                    idx,
                    len(audio_data),
                    len(tts_result.timestamps)
                )

                audio_duration = tts_service.get_audio_duration(audio_data)
                logger.info("subtitle[%s] re-tts audio_duration=%s seconds", idx, audio_duration)
                audio_duration_list[idx] = audio_duration  # Update audio duration

                if audio_duration > original_duration:
                    audio_speed = audio_duration / original_duration
                    logger.warning(
                        "subtitle[%s] re-tts audio_duration=%s still > original_duration=%s, will use ICE speed=%s",
                        idx,
                        audio_duration,
                        original_duration,
                        audio_speed
                    )
                    audio_data_list[idx] = audio_data
                    translated_subtitles[idx]["text"] = translated_text
                    translated_subtitles[idx]["tts_timestamps"] = tts_result.timestamps
                    translated_subtitles[idx]["audio_speed"] = audio_speed
                else:
                    audio_data_list[idx] = audio_data
                    translated_subtitles[idx]["text"] = translated_text
                    translated_subtitles[idx]["tts_timestamps"] = tts_result.timestamps
                    translated_subtitles[idx]["audio_speed"] = 1.0
                    logger.info("subtitle[%s] replaced with shortened translation", idx)

        # Step 3.5: Apply continuous dubbing alignment if enabled
        if request.continuous_dubbing:
            logger.info("Continuous dubbing mode enabled, calculating alignment strategies")
            alignment_strategies = continuous_dubbing_service.calculate_alignment_strategy(
                original_subtitles,
                translated_subtitles,
                audio_duration_list
            )

            # Apply TTS speed adjustments and update audio data
            for strategy in alignment_strategies:
                idx = strategy["index"]
                tts_speed = strategy["tts_speed"]

                # Apply TTS speed adjustment if needed
                if tts_speed > 1.01:  # Only adjust if speed is significantly > 1.0
                    logger.info(
                        "subtitle[%s] applying TTS speed adjustment speed=%s",
                        idx,
                        tts_speed
                    )
                    original_audio = audio_data_list[idx]
                    adjusted_audio = await continuous_dubbing_service.adjust_audio_speed(
                        original_audio,
                        tts_speed
                    )
                    audio_data_list[idx] = adjusted_audio

                    # Update audio duration after speed adjustment
                    new_duration = tts_service.get_audio_duration(adjusted_audio)
                    audio_duration_list[idx] = new_duration
                    logger.info(
                        "subtitle[%s] TTS speed adjusted original_duration=%s new_duration=%s",
                        idx,
                        strategy["tts_duration"],
                        new_duration
                    )

                # Update subtitle timestamps and speeds
                translated_subtitles[idx]["start_time"] = strategy["adjusted_start"]
                translated_subtitles[idx]["end_time"] = strategy["adjusted_end"]
                translated_subtitles[idx]["audio_speed"] = 1.0  # Audio already adjusted
                translated_subtitles[idx]["video_speed"] = strategy["video_speed"]
                translated_subtitles[idx]["continuous_dubbing"] = True

                logger.info(
                    "subtitle[%s] continuous dubbing alignment applied: "
                    "original[%s-%s] -> adjusted[%s-%s], "
                    "tts_speed=%s, video_speed=%s, final_duration=%s",
                    idx,
                    strategy["original_start"],
                    strategy["original_end"],
                    strategy["adjusted_start"],
                    strategy["adjusted_end"],
                    strategy["tts_speed"],
                    strategy["video_speed"],
                    strategy["final_duration"]
                )

        # Step 4: Upload and register audio segments
        for index, translated_subtitle in enumerate(translated_subtitles):
            audio_data = audio_data_list[index]
            if audio_data is None:
                logger.info("subtitle[%s] skipped due to duration constraint", index)
                continue

            current_start_time = translated_subtitle["start_time"]
            current_end_time = translated_subtitle["end_time"]
            translated_text = translated_subtitle["text"]

            audio_media_id = None
            if audio_data:
                audio_key = oss_service.upload_audio(audio_data)
                logger.info("subtitle[%s] audio uploaded oss_key=%s", index, audio_key)
                audio_url = oss_service.get_file_url(audio_key)
                audio_media_id = ice_service.register_media(
                    input_url=audio_url,
                    title=audio_key,
                    media_type="audio"
                )
                logger.info("subtitle[%s] audio registered media_id=%s input_url=%s", index, audio_media_id, audio_url)

            audio_segments.append(
                {
                    "index": index,
                    "translated_text": translated_text,
                    "start_time": current_start_time,
                    "end_time": current_end_time,
                    "audio_media_id": audio_media_id,
                    "audio_speed": translated_subtitle.get("audio_speed", 1.0),
                    "video_speed": translated_subtitle.get("video_speed", 1.0),
                    "audio_duration": audio_duration_list[index] if index < len(audio_duration_list) else 0.0,
                    "tts_timestamps": translated_subtitle.get("tts_timestamps", []),
                    "continuous_dubbing": translated_subtitle.get("continuous_dubbing", False)
                }
            )

        # Convert subtitle params to ICE field names
        subtitle_params_dict = None
        if request.subtitle_params:
            subtitle_params_dict = {
                key: value
                for key, value in {
                    "Alignment": request.subtitle_params.alignment,
                    "Font": request.subtitle_params.font,
                    "FontSize": request.subtitle_params.font_size,
                    "FontColor": request.subtitle_params.font_color,
                    "Outline": request.subtitle_params.outline,
                    "OutlineColour": request.subtitle_params.outline_colour,
                    "BackColour": request.subtitle_params.back_colour,
                    "EffectColorStyle": request.subtitle_params.effect_color_style,
                    "SubtitleEffects": request.subtitle_params.subtitle_effects,
                    "AdaptMode": request.subtitle_params.adapt_mode,
                    "Y": request.subtitle_params.y
                }.items()
                if value is not None
            }

        timeline_json = timeline_service.build_timeline(
            media_id=request.media_id,
            audio_segments=audio_segments,
            subtitle_params=subtitle_params_dict,
            background_audio_media_id=background_audio_media_id
        )
        logger.info("timeline generated task_id=%s timeline=%s", request.task_id, timeline_json)
        result_video_url = await ice_service.render(timeline_json)
        logger.info("render submitted task_id=%s result_video_url=%s", request.task_id, result_video_url)
        summary_path = _write_translation_summary(
            docker_task_id=docker_task_id,
            request=request,
            original_subtitles=original_subtitles,
            translated_subtitles=translated_subtitles,
            audio_segments=audio_segments,
            timeline_json=timeline_json,
            result_video_url=result_video_url,
            background_audio_media_id=background_audio_media_id,
        )

        return TranslateVideoResponse(
            task_id=request.task_id,
            docker_task_id=docker_task_id,
            status="processing" if result_video_url is None else "completed",
            timeline_json=timeline_json,
            result_video_url=result_video_url,
            audio_segments=audio_segments,
            tts_timestamps=[
                {
                    "index": segment["index"],
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"],
                    "translated_text": segment["translated_text"],
                    "audio_duration": segment["audio_duration"],
                    "items": segment.get("tts_timestamps", [])
                }
                for segment in audio_segments
            ],
            summary_path=summary_path,
            message="Timeline generated. ICE render is pending or not configured." if result_video_url is None else "Completed"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("translate_video failed task_id=%s", request.task_id)
        raise HTTPException(status_code=500, detail=str(e))
