"""Command handlers shared by the Discord bot and the mock CLI.

Each returns the exact string that should be shown to the user, so the two
front-ends (real Discord vs. local console) run identical logic.
"""
import backend_client as api
import formatters as fmt
from humanizer import humanize

BACKEND_DOWN = "⚠️ I couldn't reach the office backend right now — is it running on port 8000?"

HELP_TEXT = (
    "**Office Energy Monitor**\n"
    "`!status` — current state of every room\n"
    "`!room <name>` — a single room (`drawing`, `work1`, `work2`)\n"
    "`!usage` — total power draw now and energy used today\n"
    "`!alerts` — anything left running outside office hours\n"
    "I read live from the same backend as the web dashboard."
)


async def status_reply() -> str:
    try:
        rooms = await api.get_rooms()
    except Exception:
        return BACKEND_DOWN
    return await humanize(fmt.format_status(rooms), "overall office device status")


async def room_reply(name: str | None) -> str:
    if not name:
        return "Which room? Try `!room drawing`, `!room work1`, or `!room work2`."
    room_id = fmt.resolve_room(name)
    if room_id is None:
        return f"I don't recognise the room '{name}'. Try `drawing`, `work1`, or `work2`."
    try:
        room = await api.get_room(room_id)
    except Exception:
        return BACKEND_DOWN
    return await humanize(fmt.format_room(room), f"status of {room_id}")


async def usage_reply() -> str:
    try:
        usage = await api.get_usage()
    except Exception:
        return BACKEND_DOWN
    return await humanize(fmt.format_usage(usage), "current power usage and today's energy")


async def alerts_reply() -> str:
    # Already clean and scannable with severity markers -- send as-is.
    try:
        active = await api.get_alerts()
    except Exception:
        return BACKEND_DOWN
    return fmt.format_alerts(active)
