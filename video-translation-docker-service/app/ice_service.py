import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_ice20201109.client import Client as ICEClient
from alibabacloud_ice20201109 import models as ice_models
from app.config import settings
from app.oss_service import oss_service


logger = logging.getLogger("video_translation_fc.ice")


class ICEService:
    def __init__(self):
        self.enabled = bool(settings.ALIYUN_ICE_ACCESS_KEY_ID and settings.ALIYUN_ICE_ACCESS_KEY_SECRET)
        self.client = None
        if self.enabled:
            config = open_api_models.Config(
                access_key_id=settings.ALIYUN_ICE_ACCESS_KEY_ID,
                access_key_secret=settings.ALIYUN_ICE_ACCESS_KEY_SECRET
            )
            config.endpoint = settings.ALIYUN_ICE_ENDPOINT
            config.region_id = settings.ALIYUN_ICE_REGION_ID
            self.client = ICEClient(config)

    def register_media(self, input_url: str, title: str, media_type: str) -> Optional[str]:
        if not self.client:
            logger.warning("ICE register_media skipped because client is not configured title=%s media_type=%s", title, media_type)
            return None

        logger.info("ICE register_media start title=%s media_type=%s input_url=%s", title, media_type, input_url)
        request = ice_models.RegisterMediaInfoRequest(
            input_url=input_url,
            media_type=media_type,
            title=title
        )
        runtime = util_models.RuntimeOptions(
            autoretry=True,
            max_attempts=3,
            backoff_policy="no",
            backoff_period=1
        )

        try:
            response = self.client.register_media_info_with_options(request, runtime)
            logger.info("ICE register_media success title=%s media_id=%s", title, response.body.media_id)
            return response.body.media_id
        except Exception as e:
            # Handle MediaAlreadyExist error - extract existing media_id from error message
            error_str = str(e)
            if "MediaAlreadyExist" in error_str and "mediaId" in error_str:
                # Extract mediaId from error message like: 'mediaId "d5e378004cfc71f191f9f6e7c7496303"'
                import re
                match = re.search(r'mediaId\s+"([a-f0-9]+)"', error_str)
                if match:
                    existing_media_id = match.group(1)
                    logger.info("ICE register_media: media already exists, using existing media_id=%s title=%s", existing_media_id, title)
                    return existing_media_id
            # Re-raise if not MediaAlreadyExist or cannot extract media_id
            raise

    async def render(self, timeline_json: Dict[str, Any]) -> Optional[str]:
        if not self.client:
            logger.warning("ICE render skipped because client is not configured")
            return None

        output_key = f"{settings.ALIYUN_ICE_OUTPUT_PATH}/{uuid.uuid4().hex}.mp4"
        output_url = oss_service.get_file_url(output_key)
        signed_output_url = oss_service.generate_download_url(output_key)
        logger.info("ICE render start output_key=%s output_url=%s timeline=%s", output_key, output_url, timeline_json)

        # Configure output as portrait 1080p (1080x1920) with 4000 kbps bitrate
        output_config = {
            "MediaURL": output_url,
            "Width": 1080,
            "Height": 1920,
            "Bitrate": 4000
        }

        request = ice_models.SubmitMediaProducingJobRequest(
            timeline=json.dumps(timeline_json, ensure_ascii=False),
            output_media_target="oss-object",
            output_media_config=json.dumps(output_config, ensure_ascii=False),
            source="OpenAPI"
        )

        # Save ICE render parameters to log file
        self._save_render_log(timeline_json, output_config, output_key)

        response = self.client.submit_media_producing_job(request)
        logger.info("ICE render submitted response=%s signed_output_url=%s", response.body, signed_output_url)
        return signed_output_url

    def _save_render_log(self, timeline_json: Dict[str, Any], output_config: Dict[str, Any], output_key: str):
        """Save ICE render parameters to a log file"""
        try:
            # Create logs directory if it doesn't exist
            log_dir = Path("logs/ice_renders")
            log_dir.mkdir(parents=True, exist_ok=True)

            # Generate log filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"ice_render_{timestamp}.txt"
            log_path = log_dir / log_filename

            # Prepare log content
            log_content = f"""ICE Render Parameters Log
Generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Output Key: {output_key}

=== Output Configuration ===
{json.dumps(output_config, indent=2, ensure_ascii=False)}

=== Timeline Configuration ===
{json.dumps(timeline_json, indent=2, ensure_ascii=False)}

=== Subtitle Parameters (if present) ===
"""

            # Extract subtitle parameters if they exist
            if "SubtitleTracks" in timeline_json:
                for track_idx, track in enumerate(timeline_json["SubtitleTracks"]):
                    log_content += f"\nSubtitle Track {track_idx + 1}:\n"
                    if "SubtitleTrackClips" in track:
                        for clip_idx, clip in enumerate(track["SubtitleTrackClips"]):
                            log_content += f"  Clip {clip_idx + 1}:\n"
                            log_content += f"    Content: {clip.get('Content', 'N/A')}\n"
                            log_content += f"    FontSize: {clip.get('FontSize', 'N/A')}\n"
                            log_content += f"    Alignment: {clip.get('Alignment', 'N/A')}\n"
                            log_content += f"    X: {clip.get('X', 'N/A')}\n"
                            log_content += f"    Y: {clip.get('Y', 'N/A')}\n"
                            log_content += f"    FontColor: {clip.get('FontColor', 'N/A')}\n"
                            log_content += f"    Font: {clip.get('Font', 'N/A')}\n"
                            log_content += f"    Outline: {clip.get('Outline', 'N/A')}\n"
                            log_content += f"    OutlineColour: {clip.get('OutlineColour', 'N/A')}\n"
            else:
                log_content += "No subtitle tracks found\n"

            # Write to file
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(log_content)

            logger.info(f"ICE render parameters saved to {log_path}")

        except Exception as e:
            logger.error(f"Failed to save ICE render log: {e}", exc_info=True)


ice_service = ICEService()
