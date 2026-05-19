import httpx
import re
import logging
import os
import json
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)


class TranslationService:
    LANGUAGE_DISPLAY_NAMES = {
        "zh": "中文",
        "zh-cn": "中文",
        "cn": "中文",
        "en": "英语",
        "en-us": "英语",
        "en-gb": "英语",
        "ja": "日语",
        "jp": "日语",
        "ko": "韩语",
        "kr": "韩语",
        "th": "泰语",
        "thai": "泰语",
        "vi": "越南语",
        "vn": "越南语",
        "vietnamese": "越南语",
        "es": "西班牙语",
        "fr": "法语",
        "de": "德语",
        "id": "印尼语",
        "ms": "马来语",
        "fil": "菲律宾语",
        "tl": "菲律宾语",
        "ru": "俄语",
        "it": "意大利语",
        "yue": "粤语",
        "zh-hk": "粤语",
    }

    def _target_language_name(self, target_language: str) -> str:
        key = (target_language or "").strip().lower().replace("_", "-")
        return self.LANGUAGE_DISPLAY_NAMES.get(key) or self.LANGUAGE_DISPLAY_NAMES.get(key.split("-", 1)[0]) or target_language

    def _save_to_file(self, content: str, filename: str):
        """Save content to a file in logs directory."""
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        filepath = os.path.join(logs_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Saved to file: {filepath}")

    def _format_timestamp(self, time_ms: int) -> str:
        total_seconds = max(0, int(round(time_ms / 1000)))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _parse_timestamp(self, value: str) -> int:
        parts = value.strip().split(":")
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return int(round((minutes * 60 + seconds) * 1000))
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return int(round((hours * 3600 + minutes * 60 + seconds) * 1000))
        raise ValueError(f"Invalid timestamp: {value}")

    def _parse_timestamped_subtitles(self, content: str) -> list[dict]:
        pattern = re.compile(
            r"^\s*\[?(\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)\]?\s*(?:→|->|-->|-)\s*\[?(\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)\]?\s+(.+?)\s*$"
        )
        subtitles = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if not match:
                continue
            subtitles.append(
                {
                    "start_time": self._parse_timestamp(match.group(1)),
                    "end_time": self._parse_timestamp(match.group(2)),
                    "text": match.group(3).strip()
                }
            )
        return subtitles

    async def _call_gemini_chat(self, request_body: dict, endpoint: str, model: str) -> dict:
        payload = {
            **request_body,
            "model": model,
            "stream": False
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.GEMINI_BASE_URL.rstrip('/')}{endpoint}",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.GEMINI_API_KEY}"
                },
                json=payload
            )
            response.raise_for_status()
            return response.json()

    def _extract_gemini_content(self, data: dict) -> str:
        if "choices" in data:
            return data["choices"][0]["message"]["content"].strip()
        if "content" in data:
            return data["content"].strip()
        if "message" in data:
            return data["message"]["content"].strip()
        raise ValueError(f"Unknown response format: {data}")

    async def translate_subtitles_with_timestamps(self, subtitles: list, target_language: str, max_retries: int = 3) -> list[dict]:
        target_language_name = self._target_language_name(target_language)
        if not settings.GEMINI_API_KEY:
            formatted_subtitles = [
                {
                    "start_time": subtitle.get('words', [{}])[0].get('start_time', subtitle.get('start_time')) if subtitle.get('words') else subtitle.get('start_time'),
                    "end_time": subtitle.get('end_time'),
                    "text": subtitle.get('text', '')
                }
                for subtitle in subtitles
            ]
            return formatted_subtitles

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_subtitles = "\n".join(
            [
                f"{self._format_timestamp(subtitle.get('words', [{}])[0].get('start_time', subtitle.get('start_time')) if subtitle.get('words') else subtitle.get('start_time'))}\n→\n{self._format_timestamp(subtitle.get('end_time'))}\n{subtitle.get('text', '')}"
                for subtitle in subtitles
            ]
        )

        last_error = None
        endpoints = [
            ("gemini-2.5-flash", "/gemini-2.5-flash/v1/chat/completions", settings.GEMINI_MODEL, max_retries),
            ("gemini-3.1-pro", "/gemini-3.1-pro/v1/chat/completions", "gemini-3.1-pro", max_retries)
        ]

        for endpoint_name, endpoint, model, endpoint_retries in endpoints:
            for attempt in range(endpoint_retries):
                try:
                    request_body = {
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": f"你是一位专业的短视频字幕翻译官与本地化编辑，擅长将中文短视频字幕翻译成{target_language_name}，并让译文适合字幕展示和 TTS 配音。"
                            },
                            {
                                "role": "user",
                                "content": f"""# Role
你是一位专业的短视频字幕翻译官、本地化编辑和配音脚本顾问。你需要把中文短视频字幕自然、准确、精简地翻译成{target_language_name}。

# Task
将提供的中文视频字幕（带时间戳）翻译为{target_language_name}。每条字幕的开始时间和结束时间必须严格保持原样，不能重新设计、调整、合并或删除任何时间戳。译文必须保留原意，同时适合短视频字幕展示和 TTS 口播。

# Constraints & Rules
1. **目标语言唯一**：所有译文必须使用{target_language_name}。不要混入其他语言；品牌名、产品名、人名等专有名词如无通用译名，可按{target_language_name}习惯音译或保留原名。
2. **时间戳固定**：每一条字幕的开始时间和结束时间都必须与原字幕完全一致，绝对不能变动。
3. **数量固定**：输出字幕条数必须与原字幕条数保持一致，禁止合并、拆分、删除或新增字幕条目。
4. **表达自然**：不要逐字硬译。译文必须符合{target_language_name}母语使用习惯，口语化、简洁、自然。
5. **时长适配**：每条译文要尽量短，适合在对应原始时间段内朗读。时间太短时优先保留核心信息，删减冗余修饰。
6. **关键点对齐**：产品名、功能卖点、转折和收尾句等关键内容必须落在原始对应时间段内表达。
7. **输出纯净**：不要解释，不要编号，不要 Markdown，不要额外说明。

# Output Format
请严格按以下格式输出，每行一条字幕：
[开始时间] → [结束时间] {target_language_name}译文

---
# Original Subtitles to Translate:
{original_subtitles}"""
                            }
                        ]
                    }

                    request_filename = f"request_timestamped_{timestamp}_{endpoint_name}_attempt{attempt+1}.txt"
                    self._save_to_file(json.dumps(request_body, indent=2, ensure_ascii=False), request_filename)

                    data = await self._call_gemini_chat(request_body, endpoint, model)
                    logger.info(f"Gemini API timestamped response from {endpoint_name}: {data}")

                    response_filename = f"response_timestamped_{timestamp}_{endpoint_name}_attempt{attempt+1}.txt"
                    self._save_to_file(json.dumps(data, indent=2, ensure_ascii=False), response_filename)

                    translated_content = self._extract_gemini_content(data)

                    parsed_subtitles = self._parse_timestamped_subtitles(translated_content)
                    if parsed_subtitles:
                        return parsed_subtitles

                    logger.warning("No timestamped subtitles parsed from Gemini response. Retrying.")
                except Exception as e:
                    last_error = e
                    logger.warning(f"Timestamped translation {endpoint_name} attempt {attempt + 1} failed: {str(e)}")

        raise RuntimeError(f"Timestamped translation failed after fallback attempts: {str(last_error)}")

    async def translate_batch_shorten(self, texts: list[str], target_language: str, max_retries: int = 3) -> list[str]:
        target_language_name = self._target_language_name(target_language)
        """
        Translate texts with aggressive shortening for subtitles that need faster TTS.
        Returns list of shortened translated texts.
        """
        if not settings.GEMINI_API_KEY:
            return texts

        last_error = None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for attempt in range(max_retries):
            try:
                # Format texts for batch translation
                texts_formatted = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])

                request_body = {
                    "model": settings.GEMINI_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"你是专业视频字幕压缩翻译助手。请将句子翻译成{target_language_name}，并尽量压缩到适合短时间 TTS 朗读。只输出译文，不要编号，不要解释。"
                        },
                        {
                            "role": "user",
                            "content": f"请将以下{len(texts)}个句子翻译成{target_language_name}，并尽可能比常规翻译更短。\n\n强制规则：\n1. 所有译文必须使用{target_language_name}，不要混入其他语言；专有名词如无通用译名，可按{target_language_name}习惯音译或保留原名。\n2. 必须逐句对应输入，不能合并、拆分、删除或新增句子。\n3. 保留核心意思，删除冗余修饰、重复语气词和不影响理解的细节。\n4. 译文要自然、口语化，适合 TTS 配音，不要生硬直译。\n5. 优先短句、短词和常用表达；如果原句过长，可以省略次要信息。\n6. 只输出译文，每行一句，不要编号，不要解释。\n\n原文（每行一句）：\n{texts_formatted}\n\n翻译（每行一句，使用{target_language_name}，极致精简）："
                        }
                    ]
                }

                # Save request to file
                request_filename = f"request_shorten_{timestamp}_attempt{attempt+1}.txt"
                self._save_to_file(json.dumps(request_body, indent=2, ensure_ascii=False), request_filename)

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{settings.GEMINI_BASE_URL.rstrip('/')}/gemini-2.5-flash/v1/chat/completions",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {settings.GEMINI_API_KEY}"
                        },
                        json=request_body
                    )
                    response.raise_for_status()
                    data = response.json()
                    logger.info(f"Gemini API shorten response: {data}")

                    # Save response to file
                    response_filename = f"response_shorten_{timestamp}_attempt{attempt+1}.txt"
                    self._save_to_file(json.dumps(data, indent=2, ensure_ascii=False), response_filename)

                    # Try to parse response
                    if "choices" in data:
                        translated_content = data["choices"][0]["message"]["content"].strip()
                    elif "content" in data:
                        translated_content = data["content"].strip()
                    elif "message" in data:
                        translated_content = data["message"]["content"].strip()
                    else:
                        logger.warning(f"Unknown response format: {data}")
                        raise ValueError(f"Unknown response format: {data}")

                    # Parse translated lines
                    translated_lines = [line.strip() for line in translated_content.split('\n') if line.strip()]

                    # Validate we got the right number of translations
                    if len(translated_lines) != len(texts):
                        logger.warning(f"Expected {len(texts)} translations, got {len(translated_lines)}. Retrying.")
                        if attempt == max_retries - 1:
                            # Last attempt failed, return original texts
                            return texts
                        continue

                    return translated_lines

            except Exception as e:
                last_error = e
                logger.warning(f"Shorten translation attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    # Last attempt failed, return original texts
                    return texts
                continue

        # All retries failed, return original texts
        return texts

translation_service = TranslationService()
