from typing import Any, Dict, List, Optional


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

    def repair_subtitle_display_timestamps(self, subtitle_clips: List[Dict[str, Any]]) -> None:
        for index in range(len(subtitle_clips) - 1):
            current_clip = subtitle_clips[index]
            next_clip = subtitle_clips[index + 1]
            if current_clip["TimelineOut"] == next_clip["TimelineIn"]:
                current_clip["TimelineOut"] = round(current_clip["TimelineOut"] - 0.1, 4)

    def build_timeline(
        self,
        media_id: str,
        audio_segments: List[Dict[str, Any]],
        subtitle_params: Optional[Dict[str, Any]] = None,
        background_audio_media_id: Optional[str] = None
    ) -> Dict[str, Any]:
        # Default subtitle parameters
        default_subtitle_params = {
            "Alignment": "TopCenter",
            "Font": "Alibaba PuHuiTi",
            "FontSize": 84,
            "FontColor": "#ffffff",
            "Outline": 2,
            "OutlineColour": "#000000",
            "Y": 0.75
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
        
        # Calculate subtitle timeline based on TTS audio durations
        subtitle_clips = []
        for segment in audio_segments:
            audio_duration = segment.get("audio_duration", 0.0)
            if audio_duration <= 0:
                # Fallback to original timing if no audio duration
                timeline_in = round(segment["start_time"] / 1000, 4)
                timeline_out = round(segment["end_time"] / 1000, 4)
            else:
                # Use original start time, but adjust end time based on TTS duration
                timeline_in = round(segment["start_time"] / 1000, 4)
                timeline_out = round(timeline_in + audio_duration, 4)
            
            subtitle_clip = {
                "Type": "Text",
                "Content": self.manual_wrap_text(segment["translated_text"], max_chars=22),
                "TimelineIn": timeline_in,
                "TimelineOut": timeline_out,
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
        
        self.repair_subtitle_display_timestamps(subtitle_clips)

        # Add TTS audio track with corrected timing
        if audio_segments:
            audio_track_clips = []
            for segment in audio_segments:
                if segment.get("audio_media_id"):
                    audio_track_clips.append({
                        "MediaId": segment["audio_media_id"],
                        "TimelineIn": round(segment["start_time"] / 1000, 4),
                        "Speed": round(segment.get("audio_speed", 1.0), 4)
                    })
            
            audio_tracks.append({
                "AudioTrackClips": audio_track_clips
            })

        return {
            "VideoTracks": [
                {
                    "MainTrack": True,
                    "VideoTrackClips": [
                        {
                            "MediaId": media_id,
                            "Effects": [
                                {
                                    "Type": "Volume",
                                    "Gain": 0
                                }
                            ]
                        }
                    ]
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
