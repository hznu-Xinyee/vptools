"""
Script to retry failed video translation tasks for user001 in the last 24 hours.
This will resubmit the tasks to FC service with original configurations.
"""

import sys
import asyncio
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.video_translation import VideoTranslationTask, VideoTranslationStatus
from app.models.user import User
from app.services.video_translation_service import video_translation_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 并发控制：最多同时提交5个任务到FC服务
retry_semaphore = asyncio.Semaphore(5)


def _json_loads(value, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


async def retry_single_task(db: Session, task: VideoTranslationTask):
    """Retry a single failed task"""
    async with retry_semaphore:
        try:
            logger.info(f"正在重试任务 {task.id}: {task.original_filename}")

            # Parse configurations from original task
            subtitle_json = _json_loads(task.subtitle_json, {})
            target_languages = _json_loads(task.target_languages, None)

            # Determine target languages
            if target_languages:
                target_langs_list = target_languages
                target_lang = None
            else:
                target_langs_list = [task.target_language] if task.target_language else []
                target_lang = task.target_language

            # Get subtitle params (for auto translation tasks)
            subtitle_params = None
            if task.is_auto:
                # Build default subtitle params
                subtitle_params = {
                    "alignment": "TopCenter",
                    "font": "Alibaba PuHuiTi",
                    "font_size": 80,
                    "font_color": "#ffffff",
                    "outline": 2,
                    "outline_colour": "#000000",
                    "y": 0.75,
                    "adapt_mode": "AutoWrap",
                    "text_width": 0.8
                }

            # Get custom voice info
            custom_voice_voice_id = None
            if task.custom_voice_id:
                from app.models.custom_voice import CustomVoice
                custom_voice = db.query(CustomVoice).filter(
                    CustomVoice.id == task.custom_voice_id,
                    CustomVoice.is_active == True
                ).first()
                if custom_voice:
                    custom_voice_voice_id = custom_voice.voice_id

            # Reset task status to processing (but keep original timestamps)
            original_created_at = task.created_at
            original_updated_at = task.updated_at

            task.status = VideoTranslationStatus.PROCESSING
            task.error_message = None
            task.current_stage = "video_translation"

            # Preserve original timestamps
            task.created_at = original_created_at
            task.updated_at = original_updated_at

            db.commit()

            # Submit to FC service
            if task.is_auto:
                # Auto translation
                fc_response = await video_translation_service.submit_auto_translation(
                    task_id=task.id,
                    oss_key=task.video_oss_key,
                    file_url=task.video_url or task.original_video_url,
                    original_filename=task.original_filename,
                    target_language=target_lang,
                    target_languages=target_langs_list,
                    skip_subtitle_erasure=False,
                    full_screen_erase=True,
                    hide_subtitles=False,
                    subtitle_params=subtitle_params,
                    custom_voice_id=custom_voice_voice_id,
                    custom_voice_id_map=None,
                    continuous_dubbing=False,
                    use_test_version=False
                )
            else:
                # Manual translation (with uploaded subtitles)
                fc_response = await video_translation_service.submit_task(
                    media_id=task.video_oss_key,
                    subtitle_json=subtitle_json,
                    target_language=task.target_language,
                    task_id=task.id,
                    subtitle_params=subtitle_params,
                    background_audio_media_id=None,
                    background_audio_url=task.background_audio_url
                )

            logger.info(f"任务 {task.id} 已重新提交，FC响应: {fc_response}")

            # Update language_results if present
            if fc_response and 'language_results' in fc_response:
                task.language_results_json = json.dumps(fc_response['language_results'], ensure_ascii=False)

            # Restore original timestamps again after commit
            task.created_at = original_created_at
            task.updated_at = original_updated_at
            db.commit()

            return True

        except Exception as e:
            logger.error(f"重试任务 {task.id} 失败: {str(e)}", exc_info=True)
            db.rollback()
            return False


async def retry_failed_tasks():
    """Retry processing tasks for user001 that are older than 3 hours (max 20 tasks)"""
    db = SessionLocal()
    try:
        # Find user001
        user = db.query(User).filter(User.username == "user001").first()
        if not user:
            print("User 'user001' not found in database.")
            return

        print(f"Found user: {user.username} (ID: {user.id})")

        # Query processing tasks older than 3 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=3)

        print(f"查询3小时前的processing任务（创建时间早于: {cutoff_time}）")

        stuck_tasks = db.query(VideoTranslationTask).filter(
            VideoTranslationTask.user_id == user.id,
            VideoTranslationTask.status == VideoTranslationStatus.PROCESSING,
            VideoTranslationTask.created_at < cutoff_time
        ).order_by(VideoTranslationTask.created_at.asc()).limit(20).all()

        task_count = len(stuck_tasks)
        print(f"\n找到 {task_count} 个超过3小时的processing任务（最多重试20个）")
        print(f"并发控制: 最多同时提交 5 个任务到FC服务\n")

        if task_count == 0:
            return

        # Create tasks for concurrent execution
        retry_tasks = []
        for i, task in enumerate(stuck_tasks, 1):
            print(f"[{i}/{task_count}] 准备重试任务 {task.id}: {task.original_filename}")
            print(f"  目标语言: {task.target_language}")
            print(f"  是否自动翻译: {task.is_auto}")
            print(f"  创建时间: {task.created_at}")
            print(f"  当前阶段: {task.current_stage}")
            retry_tasks.append(retry_single_task(db, task))

        # Execute all retries concurrently with semaphore control
        print(f"\n开始并发提交 {task_count} 个任务...")
        results = await asyncio.gather(*retry_tasks, return_exceptions=True)

        # Count results
        success_count = sum(1 for r in results if r is True)
        failed_count = sum(1 for r in results if r is not True)

        print(f"\n重试完成:")
        print(f"  成功: {success_count}")
        print(f"  失败: {failed_count}")
        print(f"  总计: {task_count}")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    confirm = input("确认要重新提交 user001 超过2小时的processing任务吗（最多20个）？输入 'yes' 确认: ")
    if confirm.lower() == 'yes':
        asyncio.run(retry_failed_tasks())
    else:
        print("操作已取消")
