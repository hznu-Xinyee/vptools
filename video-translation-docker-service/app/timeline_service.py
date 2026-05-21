from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TimelineService:
    def manual_wrap_text(self, text: str, max_chars: int = 18) -> str:
        """Manually wrap text at spaces for English, by character for Chinese"""
        # Check if text contains English characters
        if any(c.isalpha() and ord(c) < 128 for c in text):
            # English: wrap at spaces
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                if not current_line:
                    current_line = word
                elif len(current_line) + 1 + len(word) <= max_chars:
                    current_line += " " + word
                else:
                    lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            return "\n".join(lines)
        else:
            # Chinese: wrap by character count
            if len(text) <= max_chars:
                return text
            
            lines = []
            for i in range(0, len(text), max_chars):
                lines.append(text[i:i + max_chars])
            
            return "\n".join(lines)

    def build_aligned_segments(self, audio_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        aligned_segments = []
        previous_timeline_out = 0.0

        for segment in sorted(audio_segments, key=lambda item: (item.get("start_time", 0), item.get("index", 0))):
            audio_duration = float(segment.get("audio_duration") or 0.0)
            audio_speed = float(segment.get("audio_speed") or 1.0)
            original_timeline_in = round(float(segment["start_time"]) / 1000, 4)
            original_timeline_out = round(float(segment["end_time"]) / 1000, 4)

            if audio_duration > 0:
                effective_duration = audio_duration / audio_speed if audio_speed > 0 else audio_duration
            else:
                effective_duration = max(0.0, original_timeline_out - original_timeline_in)

            timeline_in = max(original_timeline_in, previous_timeline_out)
            timeline_out = round(timeline_in + effective_duration, 4)

            if timeline_out <= timeline_in:
                raise ValueError(f"Invalid subtitle timeline for segment {segment.get('index')}: TimelineOut must be greater than TimelineIn")
            if aligned_segments and timeline_in < aligned_segments[-1]["timeline_out"]:
                raise ValueError(f"Overlapping subtitle timeline before ICE render: segment {segment.get('index')}")

            aligned_segment = dict(segment)
            aligned_segment["timeline_in"] = round(timeline_in, 4)
            aligned_segment["timeline_out"] = timeline_out
            aligned_segment["effective_audio_duration"] = round(effective_duration, 4)
            aligned_segments.append(aligned_segment)
            previous_timeline_out = timeline_out

        return aligned_segments

    def validate_subtitle_audio_alignment(
        self,
        subtitle_clips: List[Dict[str, Any]],
        audio_track_clips: List[Dict[str, Any]],
        aligned_segments: List[Dict[str, Any]]
    ) -> None:
        if len(subtitle_clips) != len(audio_track_clips):
            raise ValueError(f"Subtitle/audio clip count mismatch before ICE render: subtitles={len(subtitle_clips)} audios={len(audio_track_clips)}")

        previous_subtitle_out = 0.0
        for index, (subtitle_clip, audio_clip, segment) in enumerate(zip(subtitle_clips, audio_track_clips, aligned_segments)):
            subtitle_in = float(subtitle_clip["TimelineIn"])
            subtitle_out = float(subtitle_clip["TimelineOut"])
            audio_in = float(audio_clip["TimelineIn"])
            audio_speed = float(audio_clip.get("Speed") or 1.0)
            audio_duration = float(segment.get("audio_duration") or 0.0)
            effective_audio_duration = audio_duration / audio_speed if audio_duration > 0 and audio_speed > 0 else float(segment.get("effective_audio_duration") or 0.0)
            audio_out = round(audio_in + effective_audio_duration, 4)

            if subtitle_in < previous_subtitle_out:
                raise ValueError(f"Subtitle timestamp overlap before ICE render: index={index}")
            if round(subtitle_in, 4) != round(audio_in, 4):
                raise ValueError(f"Subtitle/TTS TimelineIn mismatch before ICE render: index={index}, subtitle={subtitle_in}, audio={audio_in}")
            if round(subtitle_out, 4) > audio_out:
                raise ValueError(f"Subtitle TimelineOut exceeds TTS TimelineOut before ICE render: index={index}, subtitle={subtitle_out}, audio={audio_out}")
            if round(audio_out - subtitle_out, 4) > 0.1:
                raise ValueError(f"Subtitle/TTS TimelineOut gap too large before ICE render: index={index}, subtitle={subtitle_out}, audio={audio_out}")

            previous_subtitle_out = subtitle_out

    def repair_equal_subtitle_boundaries(self, subtitle_clips: List[Dict[str, Any]]) -> None:
        for index in range(len(subtitle_clips) - 1):
            current_clip = subtitle_clips[index]
            next_clip = subtitle_clips[index + 1]
            if round(float(current_clip["TimelineOut"]), 4) == round(float(next_clip["TimelineIn"]), 4):
                # Calculate a safe adjustment value based on subtitle duration
                current_duration = float(current_clip["TimelineOut"]) - float(current_clip["TimelineIn"])
                adjustment = min(0.1, current_duration * 0.5)  # Use half of duration or 0.1, whichever is smaller
                adjustment = max(0.001, adjustment)  # Ensure minimum adjustment of 1ms
                
                current_clip["TimelineOut"] = round(float(current_clip["TimelineOut"]) - adjustment, 4)
                if current_clip["TimelineOut"] <= current_clip["TimelineIn"]:
                    # If still invalid, set to a very small offset from TimelineIn
                    current_clip["TimelineOut"] = round(float(current_clip["TimelineIn"]) + 0.001, 4)
                    logger.warning(f"Subtitle timestamp at index={index} too short, forced to minimal duration")

    def build_timeline(
        self,
        media_id: str,
        audio_segments: List[Dict[str, Any]],
        subtitle_params: Optional[Dict[str, Any]] = None,
        background_audio_media_id: Optional[str] = None
    ) -> Dict[str, Any]:
        # Default subtitle parameters
        default_subtitle_params = {
            "Alignment": "BottomCenter",
            "Font": "Alibaba PuHuiTi",
            "FontSize": 84,
            "FontColor": "#ffffff",
            "Outline": 2,
            "OutlineColour": "#000000",
            "Y": 0.9
        }

        # Use provided parameters or defaults
        params = {**default_subtitle_params, **(subtitle_params or {})}

        # Build audio tracks
        audio_tracks = []
        
        # Add background audio track if available (this will replace original video audio)
        if background_audio_media_id:
            audio_tracks.append({
                "AudioTrackClips": [
                    {
                        "MediaId": background_audio_media_id,
                        "TimelineIn": 0.0
                    }
                ]
            })
        
        aligned_segments = self.build_aligned_segments(audio_segments)

        # Check if continuous dubbing mode is enabled
        has_continuous_dubbing = any(seg.get("continuous_dubbing", False) for seg in aligned_segments)

        # Build video track clips
        video_track_clips = []
        if has_continuous_dubbing:
            # Continuous dubbing mode: create separate video clips for each segment with different speeds
            current_timeline_position = 0.0

            for segment in aligned_segments:
                video_speed = segment.get("video_speed", 1.0)

                # 从原始视频中取素材的时间范围（使用原始字幕的时间戳）
                original_start = segment.get("original_start", segment.get("start_time", 0)) / 1000.0  # Convert ms to seconds
                original_end = segment.get("original_end", segment.get("end_time", 0)) / 1000.0

                # 素材时长
                source_duration = original_end - original_start

                # 成片中的时长 = 素材时长 / 视频速度
                timeline_duration = source_duration / video_speed if video_speed > 0 else source_duration

                video_clip = {
                    "MediaId": media_id,
                    "In": original_start,  # 从源视频的哪里开始取
                    "Out": original_end,   # 到源视频的哪里结束
                    "TimelineIn": current_timeline_position,  # 在成片中的开始位置
                    "TimelineOut": current_timeline_position + timeline_duration,  # 在成片中的结束位置
                    "Speed": round(video_speed, 4),
                    "ScaleMode": "Cover",
                    "Effects": [
                        {
                            "Type": "Volume",
                            "Gain": -100
                        }
                    ]
                }
                video_track_clips.append(video_clip)

                # 更新下一个片段的时间线位置
                current_timeline_position += timeline_duration

                logger.info(
                    f"[Timeline] 连续口播视频片段[{segment.get('index')}]: "
                    f"源素材 {original_start:.2f}s-{original_end:.2f}s ({source_duration:.2f}s), "
                    f"速度 {video_speed:.2f}x, "
                    f"成片位置 {video_clip['TimelineIn']:.2f}s-{video_clip['TimelineOut']:.2f}s ({timeline_duration:.2f}s)"
                )
        else:
            # Normal mode: single video clip covering the entire timeline
            video_track_clips = [
                {
                    "MediaId": media_id,
                    "ScaleMode": "Cover",
                    "Effects": [
                        {
                            "Type": "Volume",
                            "Gain": -100
                        }
                    ]
                }
            ]

        # Calculate subtitle timeline based on TTS audio durations
        subtitle_clips = []
        for segment in aligned_segments:
            subtitle_clip = {
                "Type": "Text",
                "Content": self.manual_wrap_text(segment["translated_text"], max_chars=22),
                "TimelineIn": segment["timeline_in"],
                "TimelineOut": segment["timeline_out"],
                "Alignment": params.get("Alignment", "TopCenter"),
                "Font": params.get("Font", "Alibaba PuHuiTi"),
                "FontSize": params.get("FontSize", 84),
                "FontColor": params.get("FontColor", "#ffffff"),
                "Outline": params.get("Outline", 2),
                "OutlineColour": params.get("OutlineColour", "#000000")
            }
            for field in ["BackColour", "EffectColorStyle", "SubtitleEffects", "AdaptMode", "Y"]:
                if params.get(field) is not None:
                    subtitle_clip[field] = params[field]
            subtitle_clips.append(subtitle_clip)
        self.repair_equal_subtitle_boundaries(subtitle_clips)

        # Add TTS audio track with corrected timing
        if aligned_segments:
            audio_track_clips = []
            for segment in aligned_segments:
                if segment.get("audio_media_id"):
                    audio_track_clips.append({
                        "MediaId": segment["audio_media_id"],
                        "TimelineIn": segment["timeline_in"],
                        "Speed": round(segment.get("audio_speed", 1.0), 4)
                    })
            self.validate_subtitle_audio_alignment(subtitle_clips, audio_track_clips, aligned_segments)
            
            audio_tracks.append({
                "AudioTrackClips": audio_track_clips
            })

        return {
            "VideoTracks": [
                {
                    "MainTrack": True,
                    "VideoTrackClips": video_track_clips
                }
            ],
            "AudioTracks": audio_tracks,
            "SubtitleTracks": [
                {
                    "SubtitleTrackClips": subtitle_clips
                }
            ]
        }


timeline_service = TimelineService()
