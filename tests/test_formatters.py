"""Tests for the bot's factual formatters and room-name resolver.

These strings are the source of truth for the bot's replies (the LLM only
rewords them), so their correctness matters.
"""
import re

import pytest

import formatters as fmt
from helpers import frozen_store


@pytest.mark.parametrize("name,expected", [
    ("work1", "work1"),
    ("Work Room 1", "work1"),
    ("wr1", "work1"),
    ("1", "work1"),
    ("work2", "work2"),
    ("Work Room 2", "work2"),
    ("2", "work2"),
    ("drawing", "drawing"),
    ("Drawing Room", "drawing"),
    ("kitchen", None),
    ("", None),
])
def test_resolve_room_aliases(name, expected):
    assert fmt.resolve_room(name) == expected


def test_format_status_all_off():
    store, _ = frozen_store()
    rooms = [store.room_summary(r) for r in ("drawing", "work1", "work2")]
    text = fmt.format_status(rooms)
    assert text.count("all off") == 3
    assert "Drawing Room" in text and "Work Room 1" in text


def test_format_status_reports_counts():
    store, _ = frozen_store()
    store.set_status("drawing-fan-1", True)
    store.set_status("drawing-light-1", True)
    text = fmt.format_status([store.room_summary("drawing")])
    assert "1 fan and 1 light on" in text


def test_format_status_pluralizes():
    store, _ = frozen_store()
    store.set_status("work2-fan-1", True)
    store.set_status("work2-fan-2", True)
    store.set_status("work2-light-1", True)
    store.set_status("work2-light-2", True)
    text = fmt.format_status([store.room_summary("work2")])
    assert "2 fans and 2 lights on" in text


def test_format_room_includes_power():
    store, _ = frozen_store()
    store.set_status("work1-fan-1", True)   # 60 W
    text = fmt.format_room(store.room_summary("work1"))
    assert "Work Room 1" in text and "60" in text and "power" in text.lower()


def test_format_usage_contains_all_numbers():
    store, _ = frozen_store()
    store.set_status("work1-fan-1", True)   # 60 W
    usage = store.usage()
    text = fmt.format_usage(usage)
    # total, each per-room value, and kWh should all appear
    assert str(usage["total_watts"]) in text
    assert str(usage["today_kwh"]) in text
    for w in usage["per_room"].values():
        assert str(w) in text


def test_format_alerts_empty_and_nonempty():
    assert "All clear" in fmt.format_alerts([])
    sample = [
        {"severity": "warning", "room_name": "Work Room 2",
         "message": "Work Room 2 has 2 fans on after office hours."},
        {"severity": "critical", "room_name": "Work Room 1",
         "message": "All devices in Work Room 1 have been on for 3.0 hours straight."},
    ]
    out = fmt.format_alerts(sample)
    assert "Work Room 2" in out and "2 active alerts" in out
    assert "🟡" in out and "🔴" in out   # severity indicators present
