import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import websockets
from websockets.exceptions import ConnectionClosed

from app.elevenlabs_service import elevenlabs_service

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.request import CommonRequest
except ImportError:
    AcsClient = None
    CommonRequest = None

from app.config import settings

logger = logging.getLogger("video_translation_fc.tts")


@dataclass(frozen=True)
class VoiceSpec:
    voice: str
    sample_rates: Tuple[int, ...]
    default_sample_rate: int = 16000


@dataclass(frozen=True)
class TTSResult:
    audio_data: bytes
    timestamps: List[Dict[str, Any]]


_BUILTIN_VOICE_MAP = {
    "zh": VoiceSpec(voice="xiaoyun", sample_rates=(8000, 16000)),
    "en": VoiceSpec(voice="abby_ecmix", sample_rates=(8000, 16000, 24000)),
    "ja": VoiceSpec(voice="tomoka", sample_rates=(8000, 16000)),
    "ko": VoiceSpec(voice="Kyong", sample_rates=(8000, 16000)),
    "th": VoiceSpec(voice="waan", sample_rates=(8000, 16000)),
    "vi": VoiceSpec(voice="tien", sample_rates=(8000, 16000)),
    "es": VoiceSpec(voice="camila", sample_rates=(8000, 16000)),
    "fr": VoiceSpec(voice="clara", sample_rates=(8000, 16000)),
    "de": VoiceSpec(voice="hanna", sample_rates=(8000, 16000)),
    "id": VoiceSpec(voice="indah", sample_rates=(8000, 16000)),
    "ms": VoiceSpec(voice="farah", sample_rates=(8000, 16000)),
    "fil": VoiceSpec(voice="tala", sample_rates=(8000, 16000)),
    "ru": VoiceSpec(voice="masha", sample_rates=(8000, 16000)),
    "it": VoiceSpec(voice="perla", sample_rates=(8000, 16000)),
    "yue": VoiceSpec(voice="kelly", sample_rates=(8000, 16000)),
}


_LANGUAGE_ALIASES = {
    "zh": "zh", "zh-cn": "zh", "zh_cn": "zh", "cn": "zh", "chinese": "zh", "mandarin": "zh", "中文": "zh", "普通话": "zh",
    "en": "en", "en-us": "en", "en_us": "en", "en-gb": "en", "en_gb": "en", "english": "en", "英语": "en", "英文": "en",
    "ja": "ja", "jp": "ja", "ja-jp": "ja", "ja_jp": "ja", "japanese": "ja", "日语": "ja", "日文": "ja",
    "ko": "ko", "kr": "ko", "ko-kr": "ko", "ko_kr": "ko", "korean": "ko", "韩语": "ko", "韩文": "ko",
    "th": "th", "thai": "th", "泰语": "th",
    "vi": "vi", "vn": "vi", "vietnamese": "vi", "越南语": "vi",
    "es": "es", "spanish": "es", "西班牙语": "es",
    "fr": "fr", "french": "fr", "法语": "fr",
    "de": "de", "german": "de", "德语": "de",
    "id": "id", "indonesian": "id", "印尼语": "id",
    "ms": "ms", "malay": "ms", "马来语": "ms",
    "fil": "fil", "tl": "fil", "tagalog": "fil", "filipino": "fil", "菲律宾语": "fil",
    "ru": "ru", "russian": "ru", "俄语": "ru",
    "it": "it", "italian": "it", "意大利语": "it",
    "yue": "yue", "cantonese": "yue", "zh-hk": "yue", "zh_hk": "yue", "zh-yue": "yue", "粤语": "yue", "香港粤语": "yue",
}

_PUNCTUATION_SPLIT = re.compile(r"(?<=[。!?！？.\n])\s*|(?<=[,，;；])\s+")


def _normalize_language(language: str) -> str:
    if not language:
        raise ValueError("target language is required for TTS")
    key = language.strip().lower().replace("_", "-")
    canonical = _LANGUAGE_ALIASES.get(key)
    if canonical:
        return canonical
    base = key.split("-", 1)[0]
    canonical = _LANGUAGE_ALIASES.get(base)
    if canonical:
        return canonical
    raise ValueError(f"unsupported target language for TTS: {language!r}")


def _load_voice_map() -> dict:
    voice_map = dict(_BUILTIN_VOICE_MAP)
    raw = settings.ALIYUN_NLS_VOICE_MAP_JSON
    if not raw:
        return voice_map
    try:
        overrides = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("ALIYUN_NLS_VOICE_MAP_JSON is not valid JSON, ignoring: %s", exc)
        return voice_map
    if not isinstance(overrides, dict):
        logger.warning("ALIYUN_NLS_VOICE_MAP_JSON must be a JSON object, ignoring")
        return voice_map
    for key, spec in overrides.items():
        canonical = _LANGUAGE_ALIASES.get(str(key).strip().lower())
        if not canonical or not isinstance(spec, dict):
            continue
        voice = spec.get("voice")
        if not voice:
            continue
        try:
            sample_rates = tuple(int(r) for r in (spec.get("sample_rates") or [16000]))
        except (TypeError, ValueError):
            sample_rates = (16000,)
        try:
            default_sample_rate = int(spec.get("default_sample_rate") or 16000)
        except (TypeError, ValueError):
            default_sample_rate = 16000
        if default_sample_rate not in sample_rates:
            default_sample_rate = sample_rates[0]
        voice_map[canonical] = VoiceSpec(
            voice=voice,
            sample_rates=sample_rates,
            default_sample_rate=default_sample_rate,
        )
    return voice_map


def _split_text(text: str, max_length: int) -> List[str]:
    if len(text) <= max_length:
        return [text]
    parts: List[str] = []
    buffer = ""
    for piece in _PUNCTUATION_SPLIT.split(text):
        if not piece:
            continue
        if len(buffer) + len(piece) <= max_length:
            buffer += piece
            continue
        if buffer:
            parts.append(buffer)
            buffer = ""
        while len(piece) > max_length:
            parts.append(piece[:max_length])
            piece = piece[max_length:]
        buffer = piece
    if buffer:
        parts.append(buffer)
    return parts


class TTSService:
    def __init__(self):
        self._voice_map = _load_voice_map()
        self._cached_token: Optional[str] = settings.ALIYUN_NLS_TOKEN
        self._cached_token_expire_time: int = 0
        self._token_lock = asyncio.Lock()

    def resolve_voice(self, language: str) -> Tuple[VoiceSpec, str]:
        canonical = _normalize_language(language)
        spec = self._voice_map.get(canonical)
        if not spec:
            raise ValueError(f"no Cosy TTS voice configured for language: {language!r}")
        return spec, canonical

    def _choose_sample_rate(self, spec: VoiceSpec) -> int:
        configured = settings.ALIYUN_NLS_SAMPLE_RATE
        if configured in spec.sample_rates:
            return configured
        logger.warning(
            "configured sample_rate=%s not supported by voice=%s, falling back to %s",
            configured,
            spec.voice,
            spec.default_sample_rate,
        )
        return spec.default_sample_rate

    async def synthesize(self, text: str, language: str, voice_id: Optional[str] = None) -> bytes:
        return (await self.synthesize_with_timestamps(text, language, voice_id)).audio_data

    async def synthesize_with_timestamps(self, text: str, language: str, voice_id: Optional[str] = None) -> TTSResult:
        if not text or not text.strip():
            return TTSResult(audio_data=b"", timestamps=[])

        # Use ElevenLabs if custom voice_id is provided
        if voice_id:
            logger.info(f"Using ElevenLabs TTS with voice_id={voice_id}")
            try:
                audio_data = await elevenlabs_service.synthesize(text, voice_id)
                return TTSResult(audio_data=audio_data, timestamps=[])
            except Exception as e:
                logger.error(f"ElevenLabs TTS failed, falling back to Aliyun: {str(e)}")

        if not settings.ALIYUN_NLS_APPKEY:
            logger.warning("Aliyun NLS appkey is not configured, skipping TTS")
            return TTSResult(audio_data=b"", timestamps=[])
        if not settings.ALIYUN_NLS_TOKEN and not self._has_token_credentials():
            logger.warning("Aliyun NLS token or token credentials are not configured, skipping TTS")
            return TTSResult(audio_data=b"", timestamps=[])

        spec, canonical = self.resolve_voice(language)
        sample_rate = self._choose_sample_rate(spec)

        chunks = _split_text(text, settings.ALIYUN_NLS_MAX_TEXT_LENGTH)
        audio_segments: List[bytes] = []
        all_timestamps: List[Dict[str, Any]] = []
        time_offset_ms = 0
        for index, chunk in enumerate(chunks):
            logger.info(
                "tts synthesize lang=%s voice=%s sample_rate=%s chunk=%s/%s len=%s",
                canonical,
                spec.voice,
                sample_rate,
                index + 1,
                len(chunks),
                len(chunk),
            )
            result = await self._synthesize_one(chunk, spec.voice, sample_rate)
            audio_segments.append(result.audio_data)
            shifted = self._shift_timestamps(result.timestamps, time_offset_ms, index)
            all_timestamps.extend(shifted)
            time_offset_ms = max(
                time_offset_ms + int(round(self.get_audio_duration(result.audio_data) * 1000)),
                max((item.get("end_time", 0) for item in all_timestamps), default=0),
            )

        audio_data = audio_segments[0] if len(audio_segments) == 1 else self._concat_mp3(audio_segments)
        return TTSResult(audio_data=audio_data, timestamps=all_timestamps)

    async def _synthesize_one(self, text: str, voice: str, sample_rate: int) -> TTSResult:
        token = await self._get_token()
        url = self._build_ws_url(token)
        start_message = {
            "header": {
                "message_id": uuid.uuid4().hex,
                "task_id": uuid.uuid4().hex,
                "namespace": "SpeechSynthesizer",
                "name": "StartSynthesis",
                "appkey": settings.ALIYUN_NLS_APPKEY,
            },
            "payload": {
                "text": text,
                "voice": voice,
                "format": settings.ALIYUN_NLS_FORMAT,
                "sample_rate": sample_rate,
                "volume": settings.ALIYUN_NLS_VOLUME,
                "speech_rate": settings.ALIYUN_NLS_SPEECH_RATE,
                "pitch_rate": settings.ALIYUN_NLS_PITCH_RATE,
                "enable_subtitle": True,
            },
        }
        try:
            return await asyncio.wait_for(
                self._run_ws(url, start_message),
                timeout=settings.ALIYUN_NLS_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise RuntimeError(
                f"Aliyun NLS TTS timed out after {settings.ALIYUN_NLS_TIMEOUT_SECONDS}s"
            ) from exc

    async def _run_ws(self, url: str, start_message: dict) -> TTSResult:
        audio_chunks: List[bytes] = []
        timestamps: List[Dict[str, Any]] = []
        completed = False
        async with websockets.connect(url, max_size=None) as ws:
            await ws.send(json.dumps(start_message))
            while True:
                try:
                    message = await ws.recv()
                except ConnectionClosed:
                    break
                if isinstance(message, (bytes, bytearray)):
                    audio_chunks.append(bytes(message))
                    continue
                event = self._parse_event(message)
                header = event.get("header", {})
                name = header.get("name")
                status = header.get("status")
                if name == "MetaInfo" and status == 20000000:
                    timestamps.extend(event.get("payload", {}).get("subtitles", []) or [])
                    continue
                if name == "SynthesisCompleted" and status == 20000000:
                    completed = True
                    break
                if name == "TaskFailed" or (status is not None and status != 20000000):
                    raise RuntimeError(
                        "Aliyun NLS TTS failed: "
                        f"name={name} status={status} "
                        f"message={self._event_message(header)}"
                    )
        if not completed:
            raise RuntimeError("Aliyun NLS TTS connection closed before completion")
        if not audio_chunks:
            raise RuntimeError("Aliyun NLS TTS returned no audio data")
        return TTSResult(audio_data=b"".join(audio_chunks), timestamps=timestamps)

    @staticmethod
    def _shift_timestamps(
        timestamps: List[Dict[str, Any]],
        time_offset_ms: int,
        chunk_index: int,
    ) -> List[Dict[str, Any]]:
        shifted = []
        for item in timestamps:
            copied = dict(item)
            copied["chunk_index"] = chunk_index
            if "begin_time" in copied:
                copied["begin_time"] = int(copied["begin_time"]) + time_offset_ms
            if "end_time" in copied:
                copied["end_time"] = int(copied["end_time"]) + time_offset_ms
            shifted.append(copied)
        return shifted

    def _has_token_credentials(self) -> bool:
        return bool(settings.ALIYUN_NLS_ACCESS_KEY_ID and settings.ALIYUN_NLS_ACCESS_KEY_SECRET)

    async def _get_token(self) -> str:
        if settings.ALIYUN_NLS_TOKEN:
            return settings.ALIYUN_NLS_TOKEN
        now = int(time.time())
        refresh_at = self._cached_token_expire_time - settings.ALIYUN_NLS_TOKEN_REFRESH_MARGIN_SECONDS
        if self._cached_token and now < refresh_at:
            return self._cached_token
        async with self._token_lock:
            now = int(time.time())
            refresh_at = self._cached_token_expire_time - settings.ALIYUN_NLS_TOKEN_REFRESH_MARGIN_SECONDS
            if self._cached_token and now < refresh_at:
                return self._cached_token
            token, expire_time = await asyncio.to_thread(self._create_token)
            self._cached_token = token
            self._cached_token_expire_time = expire_time
            logger.info("Aliyun NLS token refreshed, expire_time=%s", expire_time)
            return token

    def _create_token(self) -> Tuple[str, int]:
        if AcsClient is None or CommonRequest is None:
            raise RuntimeError("aliyun-python-sdk-core is required to fetch Aliyun NLS token")
        if not self._has_token_credentials():
            raise RuntimeError("Aliyun NLS AccessKey credentials are not configured")
        client = AcsClient(
            settings.ALIYUN_NLS_ACCESS_KEY_ID,
            settings.ALIYUN_NLS_ACCESS_KEY_SECRET,
            settings.ALIYUN_NLS_TOKEN_REGION_ID,
        )
        request = CommonRequest()
        request.set_method("POST")
        request.set_domain(settings.ALIYUN_NLS_TOKEN_DOMAIN)
        request.set_version("2019-02-28")
        request.set_action_name("CreateToken")
        response = client.do_action_with_exception(request)
        data = json.loads(response)
        token_data = data.get("Token") or {}
        token = token_data.get("Id")
        expire_time = token_data.get("ExpireTime")
        if not token or not expire_time:
            raise RuntimeError(f"Aliyun NLS CreateToken returned invalid response: {data}")
        return token, int(expire_time)

    def _build_ws_url(self, token: str) -> str:
        base = settings.ALIYUN_NLS_URL
        if not token:
            return base
        separator = "&" if "?" in base else "?"
        return f"{base}{separator}token={token}"

    @staticmethod
    def _parse_event(message: str) -> dict:
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _event_message(header: dict) -> str:
        return (
            header.get("status_message")
            or header.get("status_text")
            or header.get("message")
            or ""
        )

    def get_audio_duration(self, audio_data: bytes) -> float:
        if not audio_data:
            return 0.0
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as input_file:
            input_path = input_file.name
            input_file.write(audio_data)
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                input_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as exc:
            logger.warning("Error getting audio duration: %s", exc)
            return 0.0
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)

    def _concat_mp3(self, audio_data_list: List[bytes]) -> bytes:
        if not audio_data_list:
            return b""
        if len(audio_data_list) == 1:
            return audio_data_list[0]

        list_path: Optional[str] = None
        output_path: Optional[str] = None
        file_paths: List[str] = []
        try:
            for audio in audio_data_list:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as part:
                    part.write(audio)
                    file_paths.append(part.name)
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as list_file:
                list_path = list_file.name
                for path in file_paths:
                    list_file.write(f"file '{path}'\n")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as out_file:
                output_path = out_file.name
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", list_path, "-c", "copy", output_path,
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            with open(output_path, "rb") as fh:
                return fh.read()
        except Exception as exc:
            logger.warning("Error concatenating audio: %s", exc)
            return b""
        finally:
            for path in file_paths:
                if os.path.exists(path):
                    os.unlink(path)
            if list_path and os.path.exists(list_path):
                os.unlink(list_path)
            if output_path and os.path.exists(output_path):
                os.unlink(output_path)


tts_service = TTSService()
