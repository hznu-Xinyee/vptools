import asyncio
import logging
import json
import os
import subprocess
import tempfile
import requests
import httpx
from typing import Any, Dict, List, Optional
from app.ata_service import ata_service
from app.volcengine_service import volcengine_service
from app.mediakit_service import mediakit_service
from app.oss_service import oss_service
from app.ice_service import ice_service
from app.translation_service import translation_service
from app.config import settings

logger = logging.getLogger(__name__)


class AutoTranslationService:
    def __init__(self):
        self.max_concurrent_tasks = 10
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

    async def process_auto_translation(
        self,
        task_id: int,
        oss_key: str,
        file_url: str,
        original_filename: str,
        target_languages: List[str],
        skip_subtitle_erasure: bool = False,
        subtitle_params: Optional[Dict[str, Any]] = None,
        custom_voice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process auto translation workflow"""
        logger.info(f"[自动翻译] 任务 {task_id} 已进入后台队列")
        async with self.semaphore:
            return await self._process_auto_translation(
                task_id,
                oss_key,
                file_url,
                original_filename,
                target_languages,
                skip_subtitle_erasure,
                subtitle_params,
                custom_voice_id
            )

    async def _process_auto_translation(
        self,
        task_id: int,
        oss_key: str,
        file_url: str,
        original_filename: str,
        target_languages: List[str],
        skip_subtitle_erasure: bool = False,
        subtitle_params: Optional[Dict[str, Any]] = None,
        custom_voice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run one auto translation workflow after acquiring queue slot"""
        try:
            logger.info(f"[自动翻译] 任务 {task_id} 已获得处理槽位，开始执行")
            logger.info(f"[自动翻译] 开始自动翻译工作流，任务ID: {task_id}")
            logger.info(f"[自动翻译] 文件: {original_filename}, 目标语言: {', '.join(target_languages)}")
            
            # Step 1: Audio Separation and Subtitle Extraction
            logger.info(f"[自动翻译] 步骤 1/3: 开始声伴分离与字幕提取，任务ID: {task_id}")
            
            logger.info(f"[自动翻译] 从 {file_url} 下载视频")
            video_response = requests.get(file_url, timeout=30)
            video_response.raise_for_status()
            video_data = video_response.content
            logger.info(f"[自动翻译] 视频下载完成，大小: {len(video_data)} 字节")

            voice_audio_url = None
            original_audio_url = None
            background_audio_url = None
            logger.info(f"[自动翻译] 步骤 1.1/3: 开始音频分离（声伴分离）")
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
                logger.info(f"[自动翻译] 原始音频已上传到OSS，预签名URL: {original_audio_url}")

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
                            logger.info(f"[自动翻译] 背景音URL已保存: {background_audio_url}")
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
            logger.info(f"[自动翻译] 已提交到ATA，任务ID: {ata_task_id}")

            # Wait for completion
            max_attempts = 60
            logger.info(f"[自动翻译] 等待字幕提取完成（最多 {max_attempts} 次尝试）")
            subtitle_data = None
            for attempt in range(max_attempts):
                await asyncio.sleep(10)
                try:
                    ata_status = await ata_service.get_task_status(ata_task_id)
                    logger.info(f"[自动翻译] ATA状态检查 {attempt + 1}/{max_attempts}: {ata_status.get('code')}")
                    if ata_service.is_task_completed(ata_status):
                        subtitle_data = ata_status.get("utterances", [])
                        logger.info(f"[自动翻译] 字幕提取成功完成，获取到 {len(subtitle_data)} 条字幕")
                        break
                    elif ata_service.is_task_failed(ata_status):
                        logger.error(f"[自动翻译] 字幕提取失败: {ata_status}")
                        raise Exception(f"字幕提取失败")
                except Exception as e:
                    logger.warning(f"[自动翻译] ATA状态检查第 {attempt + 1} 次失败: {str(e)}")
                    if attempt >= max_attempts - 1:
                        raise
                    await asyncio.sleep(10)

            if not subtitle_data:
                raise Exception("字幕提取失败，无法获取字幕数据")

            erasure_video_url = None
            if skip_subtitle_erasure:
                logger.info(f"[自动翻译] 步骤 2/3: 已开启跳过字幕擦除，任务ID: {task_id}")
            else:
                # Step 2: Subtitle Erasure
                logger.info(f"[自动翻译] 步骤 2/3: 执行字幕擦除，任务ID: {task_id}")

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
                erasure_video_oss_key = f"auto_translate_erased/{task_id}_{original_filename}"
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as erased_video_file:
                    erased_video_path = erased_video_file.name
                    with requests.get(erasure_video_url, timeout=300, stream=True) as erasure_response:
                        erasure_response.raise_for_status()
                        for chunk in erasure_response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                erased_video_file.write(chunk)
                try:
                    with open(erased_video_path, "rb") as erased_video_data:
                        oss_service.upload_file(
                            erasure_video_oss_key,
                            erased_video_data,
                            content_type="video/mp4"
                        )
                finally:
                    if os.path.exists(erased_video_path):
                        os.unlink(erased_video_path)
                final_video_ice_url = f"oss://{settings.OSS_BUCKET_NAME}/{erasure_video_oss_key}"
                logger.info(f"[自动翻译] 字幕擦除结果已上传到OSS用于ICE注册: {final_video_ice_url}")
            elif oss_key:
                final_video_ice_url = f"oss://{settings.OSS_BUCKET_NAME}/{oss_key}"
                logger.info(f"[自动翻译] 使用原视频OSS地址注册ICE: {final_video_ice_url}")

            # Register video with ICE
            logger.info(f"[自动翻译] 在ICE中注册视频: {final_video_ice_url}")
            media_id = ice_service.register_media(final_video_ice_url, oss_key, "video")
            logger.info(f"[自动翻译] 视频已在ICE中注册，媒体ID: {media_id}")

            # Register background audio to ICE if available
            background_audio_media_id = None
            current_background_audio_url = background_audio_url
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
            
            # Step 3: Submit video translation for each target language
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

            language_results = {}
            first_language = target_languages[0]
            failed_language = None
            has_pending_language = False
            
            for target_language in target_languages:
                logger.info(f"[自动翻译] 提交 {target_language} 视频翻译到Docker服务")
                language_results[target_language] = {
                    **language_results.get(target_language, {}),
                    "status": "processing",
                }

                try:
                    docker_response = await self._submit_video_translation(
                        media_id=media_id,
                        subtitle_json=subtitle_data,
                        target_language=target_language,
                        task_id=task_id,
                        subtitle_params=subtitle_params_for_render,
                        background_audio_media_id=background_audio_media_id,
                        background_audio_url=current_background_audio_url,
                        custom_voice_id=custom_voice_id
                    )
                    logger.info(f"[自动翻译] {target_language} Docker服务响应: {docker_response}")
                except Exception as exc:
                    logger.error(f"[自动翻译] {target_language} 视频翻译失败: {str(exc)}", exc_info=True)
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

                if result_status == "failed":
                    failed_language = target_language
                    break
                if result_status != "completed":
                    has_pending_language = True

            if failed_language:
                logger.error(f"[自动翻译] 任务 {task_id} 的 {failed_language} 视频翻译失败")
                await self._notify_backend(
                    task_id,
                    "failed",
                    language_results,
                    error_message=language_results[failed_language].get("error_message")
                )
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error_message": language_results[failed_language].get("error_message"),
                    "language_results": language_results
                }
            else:
                if has_pending_language:
                    logger.info(f"[自动翻译] 任务 {task_id} 的视频翻译已提交，等待渲染完成")
                    await self._notify_backend(
                        task_id,
                        "processing",
                        language_results
                    )
                    return {
                        "task_id": task_id,
                        "status": "processing",
                        "language_results": language_results
                    }
                else:
                    logger.info(f"[自动翻译] 任务 {task_id} 的视频翻译全部完成")
                    result_video_url = None
                    for lang_result in language_results.values():
                        if lang_result.get("result_video_url"):
                            result_video_url = lang_result["result_video_url"]
                            break
                    
                    await self._notify_backend(
                        task_id,
                        "completed",
                        language_results,
                        result_video_url=result_video_url
                    )
                    return {
                        "task_id": task_id,
                        "status": "completed",
                        "language_results": language_results,
                        "result_video_url": result_video_url
                    }
            
        except Exception as e:
            logger.error(f"[自动翻译] 自动翻译后台任务失败，任务ID: {task_id}，错误: {str(e)}", exc_info=True)
            await self._notify_backend(
                task_id,
                "failed",
                error_message=str(e)
            )
            return {
                "task_id": task_id,
                "status": "failed",
                "error_message": str(e)
            }

    async def _submit_video_translation(
        self,
        media_id: str,
        subtitle_json: Any,
        target_language: str,
        task_id: int,
        subtitle_params: Optional[Dict[str, Any]] = None,
        background_audio_media_id: Optional[str] = None,
        background_audio_url: Optional[str] = None,
        custom_voice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit video translation to the translation endpoint"""
        from app.schemas import TranslateVideoRequest
        from app.translation_service import translation_service
        from app.tts_service import tts_service
        from app.oss_service import oss_service
        from app.timeline_service import timeline_service
        from app.ice_service import ice_service
        import uuid
        
        docker_task_id = uuid.uuid4().hex
        audio_segments = []
        
        try:
            tts_voice_spec, tts_canonical_lang = tts_service.resolve_voice(target_language)
        except ValueError as exc:
            logger.warning("Unsupported target_language=%s: %s", target_language, exc)
            raise Exception(str(exc))
        
        logger.info(
            "translate_video start task_id=%s docker_task_id=%s media_id=%s target_language=%s",
            task_id,
            docker_task_id,
            media_id,
            target_language
        )

        original_subtitles = [self._subtitle_to_dict(subtitle) for subtitle in subtitle_json]
        
        # Ensure background audio media ID
        background_audio_media_id = await self._ensure_background_audio_media_id(
            background_audio_media_id, background_audio_url
        )

        # Step 1: Translate subtitles with optimized timestamps
        logger.info("Starting timestamped translation for %s subtitles", len(subtitle_json))
        translated_subtitles = await translation_service.translate_subtitles_with_timestamps(
            subtitle_json,
            target_language
        )
        logger.info("Timestamped translation completed, got %s subtitles", len(translated_subtitles))

        # Step 2: First round TTS synthesis
        audio_data_list = []
        audio_duration_list = []
        unqualified_indices = []

        for index, translated_subtitle in enumerate(translated_subtitles):
            translated_text = translated_subtitle["text"]
            current_start_time = translated_subtitle["start_time"]
            current_end_time = translated_subtitle["end_time"]
            original_duration = max(0.1, (current_end_time - current_start_time) / 1000)
            
            tts_result = await tts_service.synthesize_with_timestamps(
                translated_text,
                target_language,
                voice_id=custom_voice_id
            )
            audio_data = tts_result.audio_data
            translated_subtitle["tts_timestamps"] = tts_result.timestamps

            audio_duration = tts_service.get_audio_duration(audio_data)
            audio_duration_list.append(audio_duration)

            if audio_duration > original_duration:
                unqualified_indices.append(index)

            audio_data_list.append(audio_data)

        # Step 3: Re-translate and re-synthesize unqualified subtitles
        if unqualified_indices:
            logger.info("Found %s unqualified subtitles, re-translating with shortened text", len(unqualified_indices))
            unqualified_original_texts = [
                subtitle_json[i].get("text", "") if isinstance(subtitle_json[i], dict) else getattr(subtitle_json[i], "text", "")
                for i in unqualified_indices
            ]
            shortened_translations = await translation_service.translate_batch_shorten(
                unqualified_original_texts,
                target_language
            )

            for i, idx in enumerate(unqualified_indices):
                translated_text = shortened_translations[i]
                current_start_time = translated_subtitles[idx]["start_time"]
                current_end_time = translated_subtitles[idx]["end_time"]
                original_duration = max(0.1, (current_end_time - current_start_time) / 1000)
                
                tts_result = await tts_service.synthesize_with_timestamps(
                    translated_text,
                    target_language,
                    voice_id=custom_voice_id
                )
                audio_data = tts_result.audio_data

                audio_duration = tts_service.get_audio_duration(audio_data)
                audio_duration_list[idx] = audio_duration

                if audio_duration > original_duration:
                    audio_speed = audio_duration / original_duration
                    audio_data_list[idx] = audio_data
                    translated_subtitles[idx]["text"] = translated_text
                    translated_subtitles[idx]["tts_timestamps"] = tts_result.timestamps
                    translated_subtitles[idx]["audio_speed"] = audio_speed
                else:
                    audio_data_list[idx] = audio_data
                    translated_subtitles[idx]["text"] = translated_text
                    translated_subtitles[idx]["tts_timestamps"] = tts_result.timestamps
                    translated_subtitles[idx]["audio_speed"] = 1.0

        # Step 4: Upload and register audio segments
        for index, translated_subtitle in enumerate(translated_subtitles):
            audio_data = audio_data_list[index]
            if audio_data is None:
                continue

            current_start_time = translated_subtitle["start_time"]
            current_end_time = translated_subtitle["end_time"]
            translated_text = translated_subtitle["text"]

            audio_media_id = None
            if audio_data:
                audio_key = oss_service.upload_audio(audio_data)
                audio_url = oss_service.get_file_url(audio_key)
                audio_media_id = ice_service.register_media(
                    input_url=audio_url,
                    title=audio_key,
                    media_type="audio"
                )

            audio_segments.append(
                {
                    "index": index,
                    "translated_text": translated_text,
                    "start_time": current_start_time,
                    "end_time": current_end_time,
                    "audio_media_id": audio_media_id,
                    "audio_speed": translated_subtitle.get("audio_speed", 1.0),
                    "audio_duration": audio_duration_list[index] if index < len(audio_duration_list) else 0.0,
                    "tts_timestamps": translated_subtitle.get("tts_timestamps", [])
                }
            )

        # Convert subtitle params to ICE field names
        subtitle_params_dict = None
        if subtitle_params:
            subtitle_params_dict = {
                key: value
                for key, value in {
                    "Alignment": subtitle_params.get("alignment"),
                    "Font": subtitle_params.get("font"),
                    "FontSize": subtitle_params.get("font_size"),
                    "FontColor": subtitle_params.get("font_color"),
                    "Outline": subtitle_params.get("outline"),
                    "OutlineColour": subtitle_params.get("outline_colour"),
                    "BackColour": subtitle_params.get("back_colour"),
                    "EffectColorStyle": subtitle_params.get("effect_color_style"),
                    "SubtitleEffects": subtitle_params.get("subtitle_effects"),
                    "AdaptMode": subtitle_params.get("adapt_mode"),
                    "Y": subtitle_params.get("y")
                }.items()
                if value is not None
            }

        timeline_json = timeline_service.build_timeline(
            media_id=media_id,
            audio_segments=audio_segments,
            subtitle_params=subtitle_params_dict,
            background_audio_media_id=background_audio_media_id
        )
        result_video_url = await ice_service.render(timeline_json)

        return {
            "docker_task_id": docker_task_id,
            "status": "processing" if result_video_url is None else "completed",
            "timeline_json": timeline_json,
            "result_video_url": result_video_url,
            "audio_segments": audio_segments,
            "tts_timestamps": [
                {
                    "index": segment["index"],
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"],
                    "translated_text": segment["translated_text"],
                    "audio_duration": segment["audio_duration"],
                    "items": segment.get("tts_timestamps", [])
                }
                for segment in audio_segments
            ]
        }

    def _subtitle_to_dict(self, subtitle):
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

    async def _ensure_background_audio_media_id(self, background_audio_media_id, background_audio_url):
        if background_audio_media_id:
            return background_audio_media_id
        if not background_audio_url:
            return None
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(background_audio_url)
            response.raise_for_status()
            audio_data = response.content
        
        audio_key = oss_service.upload_audio(audio_data, content_type="audio/aac")
        audio_url = oss_service.get_file_url(audio_key)
        media_id = ice_service.register_media(
            input_url=audio_url,
            title=audio_key,
            media_type="audio",
        )
        return media_id
    async def _notify_backend(self, task_id: int, status: str, language_results: Optional[Dict[str, Any]] = None, result_video_url: Optional[str] = None, error_message: Optional[str] = None):
        """Notify backend about task completion via webhook"""
        if not settings.BACKEND_URL or not settings.CALLBACK_API_KEY:
            logger.warning(f"[自动翻译] BACKEND_URL 或 CALLBACK_API_KEY 未配置，跳过回调通知")
            return
        
        callback_url = f"{settings.BACKEND_URL.rstrip('/')}/api/video-translation/fc-callback"
        payload = {
            "task_id": task_id,
            "status": status,
            "language_results": language_results,
            "result_video_url": result_video_url,
            "error_message": error_message
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    callback_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {settings.CALLBACK_API_KEY}"
                    }
                )
                response.raise_for_status()
                logger.info(f"[自动翻译] 回调通知成功，任务 {task_id}，状态 {status}")
        except Exception as e:
            logger.error(f"[自动翻译] 回调通知失败，任务 {task_id}，错误: {str(e)}")



auto_translation_service = AutoTranslationService()
