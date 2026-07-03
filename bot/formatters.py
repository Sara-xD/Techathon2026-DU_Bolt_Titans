"""Turn raw backend data into accurate factual text.

These strings are the source of truth for the bot's replies: they are fed to
the LLM to be reworded warmly, and are ALSO used verbatim as the fallback when
the LLM is unavailable. Either way the numbers come from here, never the LLM.
"""

# Accept friendly room names from users and map them to backend room ids.
ROOM_ALIASES = {
    "drawing": "drawing", "drawingroom": "drawing", "draw": "drawing",
    "work1": "work1", "workroom1": "work1", "work-1": "work1", "wr1": "work1", "1": "work1",
    "work2": "work2", "workroom2": "work2", "work-2": "work2", "wr2": "work2", "2": "work2",
}


def resolve_room(name: str) -> str | None:
    key = name.lower().replace(" ", "").replace("_", "")
    return ROOM_ALIASES.get(key)


def _room_phrase(room: dict) -> str:
    if room["fans_on"] == 0 and room["lights_on"] == 0:
        return "all off"
    return f"{room['fans_on']} fan(s) ON, {room['lights_on']} light(s) ON"


def format_status(rooms: list[dict]) -> str:
    parts = [f"{r['room_name']}: {_room_phrase(r)}" for r in rooms]
    return " | ".join(parts)


def format_room(room: dict) -> str:
    return (
        f"{room['room_name']} -> {_room_phrase(room)}. "
        f"Using {room['power']}W of power right now."
    )


def format_usage(usage: dict) -> str:
    per_room = ", ".join(
        f"{rid} {w}W" for rid, w in usage["per_room"].items()
    )
    return (
        f"Total power right now: {usage['total_watts']}W ({per_room}). "
        f"Today's estimated usage: {usage['today_kwh']} kWh."
    )


def format_alerts(alerts: list[dict]) -> str:
    if not alerts:
        return "No active alerts -- everything looks fine."
    lines = [f"{a['room_name']}: {a['message']}" for a in alerts]
    return "Active alerts -> " + " || ".join(lines)
