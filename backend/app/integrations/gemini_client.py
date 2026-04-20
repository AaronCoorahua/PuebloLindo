from __future__ import annotations

import httpx

from app.core.config import settings


async def generate_json_response(*, prompt: str, model: str) -> str:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is required to call Gemini")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={settings.gemini_api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    parts = ((candidates[0] or {}).get("content") or {}).get("parts") or []
    if not parts:
        raise RuntimeError("Gemini returned no content parts")

    text = parts[0].get("text")
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("Gemini returned empty text")
    return text
