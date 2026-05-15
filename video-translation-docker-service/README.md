# VP Video Translation Docker Service

This service receives a video media id, subtitle timestamp JSON, and target language.
It translates subtitles, synthesizes one audio segment per subtitle, uploads generated audio to OSS, builds an Aliyun ICE timeline JSON, and optionally submits the timeline to ICE for rendering.

## API

### `POST /translate-video`

Request body:

```json
{
  "task_id": 1,
  "media_id": "subtitle_erase/1/source.mov",
  "target_language": "en",
  "subtitle_json": [
    {
      "start_time": 1000,
      "end_time": 3000,
      "text": "你好",
      "words": [
        { "start_time": 1000, "end_time": 1200, "text": "你" }
      ]
    }
  ]
}
```

Response body:

```json
{
  "task_id": 1,
  "docker_task_id": "xxx",
  "status": "processing",
  "timeline_json": {},
  "result_video_url": null,
  "message": "Timeline generated. ICE render is pending or not configured."
}
```

## Run locally

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Run with Docker

```bash
docker build -t vp-video-translation-service .
docker run --env-file .env -p 8080:8080 vp-video-translation-service
```

Then set backend `.env`:

```bash
VIDEO_TRANSLATION_DOCKER_URL=http://localhost:8080
```

## Notes

- If Doubao LLM config is missing, translation returns original text.
- If Aliyun NLS/Cosy TTS appkey is missing, no audio is uploaded and `audio_media_id` is `null`.
- `ALIYUN_NLS_TOKEN` can be provided as a fixed token. If it is empty, the service fetches and refreshes tokens with `ALIYUN_NLS_ACCESS_KEY_ID` and `ALIYUN_NLS_ACCESS_KEY_SECRET` via `CreateToken`.
- Aliyun NLS does not take a separate `language` parameter; `target_language` is used to pick a voice that supports that language.
- Built-in language → voice mapping: `zh→xiaoyun`, `en→abby_ecmix`, `ja→tomoka`, `ko→Kyong`, `th→waan`, `vi→tien`, `es→camila`, `fr→clara`, `de→hanna`, `id→indah`, `ms→farah`, `fil→tala`, `ru→masha`, `it→perla`, `yue→kelly`. Override via `ALIYUN_NLS_VOICE_MAP_JSON`.
- Unsupported `target_language` values cause `/translate-video` to return HTTP 400.
- If Aliyun ICE config is missing, the service returns the generated `timeline_json` but does not render a final video.
