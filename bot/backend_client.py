"""Thin async client over the shared backend REST API.

The bot NEVER stores device state itself -- it always asks the backend, so the
bot and the web dashboard can never disagree about reality.
"""
import asyncio
import os

import aiohttp

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

# Free-tier hosts (e.g. Render) spin down when idle and take ~30-50s to wake.
# Use a generous timeout and retry connection/timeout failures so the first
# command after the backend has napped still succeeds instead of erroring out.
_TIMEOUT = aiohttp.ClientTimeout(total=float(os.getenv("BACKEND_TIMEOUT", "25")))
_RETRIES = max(1, int(os.getenv("BACKEND_RETRIES", "3")))


async def _get(path: str) -> dict:
    last_err: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BACKEND_URL}{path}", timeout=_TIMEOUT) as r:
                    r.raise_for_status()
                    return await r.json()
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
            # Connection refused / timed out -- likely a cold start. Wait and retry.
            last_err = e
            if attempt < _RETRIES - 1:
                await asyncio.sleep(2)
    raise last_err  # exhausted retries; handlers turn this into a friendly message


async def get_state() -> dict:
    return await _get("/api/state")


async def get_usage() -> dict:
    return await _get("/api/usage")


async def get_rooms() -> list[dict]:
    data = await _get("/api/rooms")
    return data["rooms"]


async def get_room(room_id: str) -> dict:
    return await _get(f"/api/rooms/{room_id}")


async def get_alerts() -> list[dict]:
    data = await _get("/api/alerts")
    return data["alerts"]
