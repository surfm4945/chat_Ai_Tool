"""Gemini integration."""

from __future__ import annotations

import httpx

from src.chat_ai_tool.config import Settings


def _build_prompt(system_prompt: str, thread_messages: list[dict[str, str]], user_request: str) -> list[dict[str, object]]:
    """Build the Gemini request payload."""

    transcript_lines = [
        f"{message['sender_username']}: {message['content']}"
        for message in thread_messages
    ]
    transcript = "\n".join(transcript_lines) if transcript_lines else "No prior messages."
    combined_prompt = (
        f"{system_prompt}\n\n"
        f"Conversation so far:\n{transcript}\n\n"
        f"User request:\n{user_request}"
    )
    return [{"role": "user", "parts": [{"text": combined_prompt}]}]


def generate_gemini_reply(
    settings: Settings,
    thread_messages: list[dict[str, str]],
    user_request: str,
) -> str:
    """Ask Gemini for a reply suggestion."""

    if not settings.gemini_api_key:
        return "Set GEMINI_API_KEY in your .env file to enable AI reply suggestions."

    payload = {
        "contents": _build_prompt(settings.ai_system_prompt, thread_messages, user_request),
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": 256,
        },
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{settings.gemini_model}:generateContent"
    )

    with httpx.Client(timeout=settings.gemini_timeout_seconds) as client:
        response = client.post(url, params={"key": settings.gemini_api_key}, json=payload)
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        return "Gemini returned no reply."

    parts = candidates[0].get("content", {}).get("parts", [])
    texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
    reply = "\n".join(texts).strip()
    return reply or "Gemini returned an empty reply."
