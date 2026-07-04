"""The simulated device layer.

There is no real hardware, so this asyncio loop stands in for it: it flips
devices on/off over time in a way that roughly follows an office day, accrues
energy, and updates room continuity. After each tick it broadcasts the full
snapshot to every connected dashboard.
"""
import asyncio
import random

from . import config
from .store import DeviceStore


def _target_on_probability(hour: int) -> float:
    """Roughly how likely a device is to be ON at a given hour of the day."""
    if config.OFFICE_OPEN_HOUR <= hour < config.OFFICE_CLOSE_HOUR:
        return 0.85          # busy office hours -> mostly on
    if config.OFFICE_CLOSE_HOUR <= hour < config.OFFICE_CLOSE_HOUR + 3:
        return 0.35          # early evening -> winding down, some forgotten
    if 6 <= hour < config.OFFICE_OPEN_HOUR:
        return 0.15          # early morning -> a few switched on
    return 0.05              # deep night -> almost everything off


class Simulator:
    def __init__(self, store: DeviceStore, broadcast):
        self.store = store
        self.broadcast = broadcast  # async callable(dict) -> None
        self._task: asyncio.Task | None = None
        self._seed_initial_state()

    def _seed_initial_state(self) -> None:
        """Start the day with a believable mix of on/off devices."""
        hour = self.store.clock.now().hour
        p = _target_on_probability(hour)
        for d in self.store.devices.values():
            if random.random() < p:
                self.store.set_status(d.id, True, by=random.choice(config.ALLOWED_ACTORS))

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()

    async def _run(self) -> None:
        while True:
            try:
                self._tick()
                await self.broadcast(self.store.snapshot())
            except asyncio.CancelledError:
                break
            except Exception as exc:  # never let the loop die silently
                print(f"[simulator] tick error: {exc}")
            await asyncio.sleep(config.SIM_TICK_SECONDS)

    def _tick(self) -> None:
        """Nudge a few random devices toward the time-appropriate occupancy."""
        hour = self.store.clock.now().hour
        target_p = _target_on_probability(hour)

        # Flip a small random subset each tick so the dashboard stays lively
        # without thrashing every device at once.
        for d in random.sample(list(self.store.devices.values()), k=3):
            wants_on = random.random() < target_p
            if wants_on != d.status:
                actor = random.choice(config.ALLOWED_ACTORS)
                self.store.set_status(d.id, wants_on, by=actor)

        self.store.refresh_readings()   # re-jitter live wattage of ON devices
        self.store.update_room_continuity()
        self.store.accrue_energy()
