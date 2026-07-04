"""The single source of truth for device state.

Both the web dashboard (via WebSocket) and the Discord bot (via REST) read
from this one store. Nothing else holds device state.

Design trade-off: state is kept in-memory rather than in a database. For 15
devices that is the simplest choice and is trivially fast for both the
WebSocket broadcast loop and REST reads; the cost is that state resets on
restart. To persist it, swap this class's internals for SQLite/SQLModel behind
the same public methods (`set_status`, `toggle`, `room_devices`, `usage`) --
those methods are the seam to do it behind.
"""
import random
from dataclasses import dataclass, field
from datetime import datetime

from . import config
from .clock import SimClock


def jitter_watts(rated: int) -> float:
    """A slightly noisy 'live current sensor' reading around the rated wattage.

    Real devices never draw exactly their nameplate rating, so we add +/- a few
    percent so the dashboard looks like it's reading a real meter, not a
    constant. Set WATT_JITTER_PCT=0 for exact, deterministic values (tests do).
    """
    pct = config.WATT_JITTER_PCT
    if pct <= 0:
        return float(rated)
    noise = rated * pct * (random.random() * 2 - 1)
    return round(rated + noise, 1)


@dataclass
class Device:
    id: str            # e.g. "work1-fan-1"
    label: str         # e.g. "Fan 1"
    type: str          # "fan" | "light"
    room: str          # room id, e.g. "work1"
    room_name: str     # e.g. "Work Room 1"
    watts: int         # rated power draw when ON
    status: bool = False
    current_watts: float = 0.0  # live (jittered) reading; 0 when off
    last_changed: datetime = field(default_factory=datetime.now)
    last_changed_by: str | None = None

    @property
    def power(self) -> float:
        """Instantaneous power draw right now (0 when off)."""
        return self.current_watts if self.status else 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "room": self.room,
            "room_name": self.room_name,
            "status": self.status,
            "watts": self.watts,               # rated
            "power": round(self.power, 1),      # live/jittered
            "last_changed": self.last_changed.isoformat(),
            "last_changed_by": self.last_changed_by,
        }


class DeviceStore:
    """Holds all 15 devices, accumulated energy, and per-room continuity."""

    def __init__(self, clock: SimClock):
        self.clock = clock
        self.devices: dict[str, Device] = {}
        self._build_devices()

        # Energy accounting (Watt-hours) for "usage today".
        self.energy_wh: float = 0.0
        self._last_energy_at: datetime = clock.now()
        self._energy_day = clock.now().date()

        # For the "all devices in a room ON for > N hours" alert:
        # room id -> sim-time when the room became fully ON (None if not).
        self.room_all_on_since: dict[str, datetime | None] = {r: None for r in config.ROOMS}

    # -- construction -------------------------------------------------------
    def _build_devices(self) -> None:
        now = self.clock.now()
        for room_id, room_name in config.ROOMS.items():
            for n in range(1, config.FANS_PER_ROOM + 1):
                d = Device(
                    id=f"{room_id}-fan-{n}", label=f"Fan {n}", type="fan",
                    room=room_id, room_name=room_name, watts=config.FAN_WATTS,
                    last_changed=now,
                )
                self.devices[d.id] = d
            for n in range(1, config.LIGHTS_PER_ROOM + 1):
                d = Device(
                    id=f"{room_id}-light-{n}", label=f"Light {n}", type="light",
                    room=room_id, room_name=room_name, watts=config.LIGHT_WATTS,
                    last_changed=now,
                )
                self.devices[d.id] = d

    # -- mutation -----------------------------------------------------------
    def set_status(self, device_id: str, status: bool, by: str | None = None) -> None:
        d = self.devices[device_id]
        if d.status == status:
            return
        d.status = status
        d.current_watts = jitter_watts(d.watts) if status else 0.0
        d.last_changed = self.clock.now()
        d.last_changed_by = by

    def toggle(self, device_id: str, by: str | None = None) -> "Device | None":
        """Flip one device (used by the dashboard's manual override)."""
        d = self.devices.get(device_id)
        if d is None:
            return None
        self.set_status(device_id, not d.status, by=by)
        return d

    def refresh_readings(self) -> None:
        """Re-jitter the live wattage of ON devices so the meter looks live."""
        for d in self.devices.values():
            if d.status:
                d.current_watts = jitter_watts(d.watts)

    def room_devices(self, room_id: str) -> list[Device]:
        return [d for d in self.devices.values() if d.room == room_id]

    # -- periodic bookkeeping (called each simulator tick) ------------------
    def accrue_energy(self) -> None:
        """Integrate current total power over elapsed sim-time into energy_wh."""
        now = self.clock.now()

        # Reset the daily counter when the simulated day rolls over.
        if now.date() != self._energy_day:
            self.energy_wh = 0.0
            self._energy_day = now.date()

        elapsed_h = (now - self._last_energy_at).total_seconds() / 3600.0
        if elapsed_h > 0:
            self.energy_wh += self.total_power() * elapsed_h
        self._last_energy_at = now

    def update_room_continuity(self) -> None:
        """Track since when each room has had ALL devices ON."""
        now = self.clock.now()
        for room_id in config.ROOMS:
            all_on = all(d.status for d in self.room_devices(room_id))
            if all_on and self.room_all_on_since[room_id] is None:
                self.room_all_on_since[room_id] = now
            elif not all_on:
                self.room_all_on_since[room_id] = None

    # -- reads --------------------------------------------------------------
    def total_power(self) -> float:
        return round(sum(d.power for d in self.devices.values()), 1)

    def room_power(self, room_id: str) -> float:
        return round(sum(d.power for d in self.room_devices(room_id)), 1)

    def usage(self) -> dict:
        return {
            "total_watts": self.total_power(),
            "per_room": {r: self.room_power(r) for r in config.ROOMS},
            "today_kwh": round(self.energy_wh / 1000.0, 3),
            "sim_time": self.clock.now().isoformat(),
        }

    def room_summary(self, room_id: str) -> dict:
        devs = self.room_devices(room_id)
        fans_on = sum(1 for d in devs if d.type == "fan" and d.status)
        lights_on = sum(1 for d in devs if d.type == "light" and d.status)
        return {
            "room": room_id,
            "room_name": config.ROOMS[room_id],
            "fans_on": fans_on,
            "lights_on": lights_on,
            "fans_total": config.FANS_PER_ROOM,
            "lights_total": config.LIGHTS_PER_ROOM,
            "power": self.room_power(room_id),
            "devices": [d.to_dict() for d in devs],
        }

    def snapshot(self) -> dict:
        """Full state — what gets pushed over WebSocket and read by the bot."""
        from .alerts import compute_alerts  # local import avoids a cycle
        return {
            "sim_time": self.clock.now().isoformat(),
            "devices": [d.to_dict() for d in self.devices.values()],
            "rooms": [self.room_summary(r) for r in config.ROOMS],
            "usage": self.usage(),
            "alerts": compute_alerts(self),
        }
