"""Rephrase factual office data into warm, friendly replies using Gemini.

Design rule: the LLM only changes *tone*, never *facts*. We hand it the exact
numbers and instruct it not to alter them. If Gemini is unavailable (no key,
rate-limited, network error), we fall back to the factual text itself, lightly
dressed up -- so the bot is always friendly and always correct.
"""
import asyncio
import os

_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

_client = None
_client_ready = False


def _get_client():
    """Lazily construct the Gemini client once."""
    global _client, _client_ready
    if _client_ready:
        return _client
    _client_ready = True
    if not _API_KEY or _API_KEY.startswith("your-"):
        return None
    try:
        from google import genai
        _client = genai.Client(api_key=_API_KEY)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[humanizer] Gemini init failed, using fallback: {exc}")
        _client = None
    return _client


SYSTEM_STYLE = (
    "You are a friendly office assistant bot for a boss who hates robotic data "
    "dumps. Rephrase the facts below into ONE or TWO warm, natural sentences. "
    "Keep it upbeat and you may use a tasteful emoji. CRITICAL: do not change, "
    "add, or drop any numbers, room names, or on/off states -- only change the "
    "wording. Do not invent information."
)


def _fallback(facts: str) -> str:
    return facts


def _blocking_generate(facts: str, context: str) -> str:
    client = _get_client()
    if client is None:
        return _fallback(facts)
    try:
        from google.genai import types
        prompt = f"{SYSTEM_STYLE}\n\nContext: {context}\nFacts: {facts}"
        resp = client.models.generate_content(
            model=_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=400,
                # Disable "thinking" so 2.5-flash replies fast and doesn't spend
                # the output budget on reasoning tokens (would truncate replies).
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        text = (resp.text or "").strip()
        return text or _fallback(facts)
    except Exception as exc:
        print(f"[humanizer] Gemini call failed, using fallback: {exc}")
        return _fallback(facts)


async def humanize(facts: str, context: str = "office status") -> str:
    """Async wrapper so the (sync) Gemini SDK never blocks the bot's event loop."""
    return await asyncio.to_thread(_blocking_generate, facts, context)
