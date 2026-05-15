import asyncio
import json

import httpx

from app.config import settings


async def main():
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    url = f"{settings.GEMINI_BASE_URL.rstrip('/')}/gemini-3.1-pro/v1/chat/completions"
    payload = {
        "model": "gemini-3.1-pro",
        "stream": False,
        "include_thoughts": False,
        "reasoning_effort": "low",
        "messages": [
            {
                "role": "user",
                "content": "请用中文回复：Gemini 3.1 Pro 接口测试成功。"
            }
        ]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.GEMINI_API_KEY}"
            },
            json=payload
        )

    print("status_code:", response.status_code)
    try:
        data = response.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        print(response.text)

    response.raise_for_status()


if __name__ == "__main__":
    asyncio.run(main())
