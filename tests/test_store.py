"""Tests for the device store: layout, power, energy accrual, continuity, usage."""
from datetime import timedelta

from app import config
from helpers import frozen_store, all_on


def test_layout_is_18_devices_6_per_room():
    store, _ = frozen_store()
    assert len(store.devices) == 18
    for room_id in config.ROOMS:
        assert len(store.room_devices(room_id)) == 6
    fans = [d for d in store.devices.values() if d.type == "fan"]
    lights = [d for d in store.devices.values() if d.type == "light"]
    assert len(fans) == 6 and len(lights) == 12


def test_device_power_ratings():
    store, _ = frozen_store()
    fan = store.devices["work1-fan-1"]
    light = store.devices["work1-light-1"]
    assert fan.watts == 60 and light.watts == 15
    assert fan.power == 0            # off -> 0
    store.set_status(fan.id, True)
    assert fan.power == 60           # on -> rated


def test_all_on_load_is_540w():
    store, _ = frozen_store()
    all_on(store)
    assert store.total_power() == 540          # 6*60 + 12*15
    assert store.room_power("work1") == 180     # 2*60 + 4*15


def test_set_status_records_actor_and_only_allowed_names():
    store, _ = frozen_store()
    store.set_status("work1-fan-1", True, by="Nafisa Rahman")
    d = store.devices["work1-fan-1"]
    assert d.status is True
    assert d.last_changed_by in config.ALLOWED_ACTORS


def test_energy_accrual_is_correct():
    store, clock = frozen_store(hour=12)
    # Exactly 90 W on: 1 fan (60) + 2 lights (30)
    store.set_status("work1-fan-1", True)
    store.set_status("work1-light-1", True)
    store.set_status("work1-light-2", True)
    assert store.total_power() == 90

    store.energy_wh = 0.0
    store._last_energy_at = clock.now()
    clock._sim_anchor += timedelta(hours=1)   # advance 1 sim hour
    store.accrue_energy()
    assert abs(store.energy_wh - 90) < 1e-6    # 90 W * 1 h = 90 Wh


def test_energy_resets_on_day_rollover():
    store, clock = frozen_store(hour=23, minute=59)
    all_on(store)
    store.energy_wh = 5000.0
    store._last_energy_at = clock.now()
    clock._sim_anchor += timedelta(minutes=2)  # cross into next day
    store.accrue_energy()
    assert store.energy_wh < 5000.0            # counter reset for the new day


def test_toggle_flips_status_and_reading():
    store, _ = frozen_store()
    d = store.toggle("work1-fan-1")          # off -> on
    assert d.status is True and d.power == 60
    store.toggle("work1-fan-1")              # on -> off
    assert store.devices["work1-fan-1"].status is False
    assert store.devices["work1-fan-1"].power == 0
    assert store.toggle("does-not-exist") is None


def test_usage_shape():
    store, _ = frozen_store()
    all_on(store)
    u = store.usage()
    assert u["total_watts"] == 540
    assert set(u["per_room"]) == set(config.ROOMS)
    assert u["today_kwh"] >= 0
    assert "sim_time" in u
