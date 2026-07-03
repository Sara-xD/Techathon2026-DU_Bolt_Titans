"""Thin async client over the shared backend REST API.

The bot NEVER stores device state itself -- it always asks the backend, so the
bot and the web dashboard can never disagree about reality.
"""
import os

import aiohttp

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")


async def _get(path: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}{path}", timeout=aiohttp.ClientTimeout(total=8)) as r:
            r.raise_for_status()
            return await r.json()


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
