"""Turn raw backend data into accurate, readable text.

These strings are the source of truth for the bot's replies: the conversational
commands feed them to the LLM to be reworded in a mature tone, and they are ALSO
used verbatim as the fallback when the LLM is unavailable. Either way the numbers
come from here, never the LLM.
"""

# Accept friendly room names from users and map them to backend room ids.
ROOM_ALIASES = {
    "drawing": "drawing", "drawingroom": "drawing", "draw": "drawing",
    "work1": "work1", "workroom1": "work1", "work-1": "work1", "wr1": "work1", "1": "work1",
    "work2": "work2", "workroom2": "work2", "work-2": "work2", "wr2": "work2", "2": "work2",
}

ROOM_NAMES = {"drawing": "Drawing Room", "work1": "Work Room 1", "work2": "Work Room 2"}

SEVERITY_EMOJI = {"critical": "🔴", "warning": "🟡"}


def resolve_room(name: str) -> str | None:
    key = name.lower().replace(" ", "").replace("_", "")
    return ROOM_ALIASES.get(key)


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _room_phrase(room: dict) -> str:
    """e.g. '1 fan and 2 lights on', '2 fans on', or 'all off'."""
    if room["fans_on"] == 0 and room["lights_on"] == 0:
        return "all off"
    parts = []
    if room["fans_on"]:
        parts.append(_plural(room["fans_on"], "fan"))
    if room["lights_on"]:
        parts.append(_plural(room["lights_on"], "light"))
    return " and ".join(parts) + " on"


def format_status(rooms: list[dict]) -> str:
    parts = [f"{r['room_name']}: {_room_phrase(r)}" for r in rooms]
    return ". ".join(parts) + "."


def format_room(room: dict) -> str:
    phrase = _room_phrase(room)
    if phrase == "all off":
        return f"{room['room_name']} is all off, using no power right now."
    return f"{room['room_name']} has {phrase}, using {room['power']}W of power right now."


def format_usage(usage: dict) -> str:
    per_room = ", ".join(
        f"{ROOM_NAMES.get(rid, rid)} {w}W" for rid, w in usage["per_room"].items()
    )
    return (
        f"The office is drawing {usage['total_watts']}W in total right now "
        f"({per_room}). Estimated energy used today: {usage['today_kwh']} kWh."
    )


def format_alerts(alerts: list[dict]) -> str:
    """A clean, scannable alert list with severity indicators (sent as-is)."""
    if not alerts:
        return "✅ All clear — no devices are running outside office hours."
    header = f"⚠️ **{len(alerts)} active alert{'s' if len(alerts) != 1 else ''}**"
    lines = [
        f"{SEVERITY_EMOJI.get(a.get('severity'), '🟡')} {a['message']}"
        for a in alerts
    ]
    return header + "\n" + "\n".join(lines)
