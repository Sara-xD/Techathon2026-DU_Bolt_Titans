"""Alert engine.

Two anomaly types the boss cares about:
  1. after_hours   - any device left ON outside office hours (9 AM-5 PM).
  2. room_all_on   - a room with all 5 devices ON continuously for > 2 hours.

Alert ids are deterministic (type:room) so the Discord bot can de-duplicate
and only announce a condition once while it stays active.
"""
from datetime import datetime

from . import config


def compute_alerts(store) -> list[dict]:
    alerts: list[dict] = []
    now: datetime = store.clock.now()
    office_hours = config.OFFICE_OPEN_HOUR <= now.hour < config.OFFICE_CLOSE_HOUR

    for room_id, room_name in config.ROOMS.items():
        devs = store.room_devices(room_id)
        on_devices = [d for d in devs if d.status]

        # 1) After-hours: devices still on when the office should be closed.
        if not office_hours and on_devices:
            fans_on = sum(1 for d in on_devices if d.type == "fan")
            lights_on = sum(1 for d in on_devices if d.type == "light")
            parts = []
            if fans_on:
                parts.append(f"{fans_on} fan" + ("" if fans_on == 1 else "s"))
            if lights_on:
                parts.append(f"{lights_on} light" + ("" if lights_on == 1 else "s"))
            alerts.append({
                "id": f"after_hours:{room_id}",
                "type": "after_hours",
                "severity": "warning",
                "room": room_id,
                "room_name": room_name,
                "message": f"{room_name} has {' and '.join(parts)} on after office hours.",
                "timestamp": now.isoformat(),
            })

        # 2) Room fully on for too long, continuously.
        since = store.room_all_on_since.get(room_id)
        if since is not None:
            hours_on = (now - since).total_seconds() / 3600.0
            if hours_on >= config.ROOM_ALL_ON_ALERT_HOURS:
                alerts.append({
                    "id": f"room_all_on:{room_id}",
                    "type": "room_all_on",
                    "severity": "critical",
                    "room": room_id,
                    "room_name": room_name,
                    "message": (
                        f"All devices in {room_name} have been on for "
                        f"{hours_on:.1f} hours straight."
                    ),
                    "timestamp": since.isoformat(),
                })

    return alerts
