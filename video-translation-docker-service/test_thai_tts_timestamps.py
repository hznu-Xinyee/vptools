import argparse
import asyncio
import json
import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parent)

from app.tts_service import tts_service


DEFAULT_TEXT = "สวัสดีครับ ยินดีต้อนรับสู่ระบบแปลวิดีโออัตโนมัติ"


async def main():
    parser = argparse.ArgumentParser(description="Generate Thai TTS audio with word timestamps.")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="Thai text to synthesize")
    parser.add_argument("--output", default="logs/thai_tts_test.mp3", help="Output MP3 path")
    parser.add_argument("--json-output", default="logs/thai_tts_timestamps.json", help="Output timestamp JSON path")
    args = parser.parse_args()

    output_path = Path(args.output)
    json_output_path = Path(args.json_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_output_path.parent.mkdir(parents=True, exist_ok=True)

    voice_spec, canonical_language = tts_service.resolve_voice("th")
    result = await tts_service.synthesize_with_timestamps(args.text, "th")
    duration = tts_service.get_audio_duration(result.audio_data)

    output_path.write_bytes(result.audio_data)

    payload = {
        "language": canonical_language,
        "voice": voice_spec.voice,
        "text": args.text,
        "audio_path": str(output_path),
        "audio_size": len(result.audio_data),
        "audio_duration": duration,
        "timestamp_count": len(result.timestamps),
        "timestamps": result.timestamps,
    }
    json_output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
