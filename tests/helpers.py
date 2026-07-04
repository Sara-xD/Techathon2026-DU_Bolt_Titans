"""Shared test helpers."""
from datetime import datetime

from app import config

# Deterministic wattage for assertions (no random current-sensor jitter).
config.WATT_JITTER_PCT = 0.0

from app.clock import SimClock
from app.store import DeviceStore


def frozen_store(hour=12, minute=0):
    """A DeviceStore whose simulated clock is frozen (speed=0) at a given time.

    Freezing makes energy/alert timing fully deterministic: `clock.now()` only
    moves when a test advances `clock._sim_anchor` itself.
    """
    start = datetime(2026, 7, 3, hour, minute, 0)
    clock = SimClock(speed=0.0, start=start)
    return DeviceStore(clock), clock


def all_on(store):
    for d in store.devices.values():
        store.set_status(d.id, True, by="Tanvir Hossain")
    store.update_room_continuity()
