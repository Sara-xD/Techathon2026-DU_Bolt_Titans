"""Central configuration and the fixed office layout.

The office setup is fixed for everyone (per the problem statement): 3 rooms,
each with 2 fans and 3 lights = 15 devices total.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Simulation tuning (read from .env) -----------------------------------
SIM_SPEED = float(os.getenv("SIM_SPEED", "60.0"))
SIM_TICK_SECONDS = float(os.getenv("SIM_TICK_SECONDS", "2.0"))
SIM_START = os.getenv("SIM_START", "").strip()  # "HH:MM" or "" for real now
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# --- Office layout (FIXED) -------------------------------------------------
# Room id -> human-readable name. Ids are what the API/bot use internally.
ROOMS = {
    "drawing": "Drawing Room",
    "work1": "Work Room 1",
    "work2": "Work Room 2",
}

# Every room has the same devices: 2 fans + 3 lights = 5 per room, 15 total
# (confirmed office layout; matches the floor plan).
FANS_PER_ROOM = 2
LIGHTS_PER_ROOM = 3

# Realistic power draw when a device is ON (Watts).
FAN_WATTS = 60
LIGHT_WATTS = 15

# Live readings jitter +/- this fraction around the rated wattage so the meter
# looks like a real current sensor rather than a constant. 0 = exact/deterministic.
WATT_JITTER_PCT = float(os.getenv("WATT_JITTER_PCT", "0.05"))

# Office hours: devices on outside this window are "after hours" (alert).
OFFICE_OPEN_HOUR = 9   # 9 AM
OFFICE_CLOSE_HOUR = 17  # 5 PM

# A room with all 5 devices ON continuously longer than this is an alert.
ROOM_ALL_ON_ALERT_HOURS = 2.0

# The ONLY people allowed as dummy actors (from the problem statement).
# Never invent additional names.
ALLOWED_ACTORS = ["Nafisa Rahman", "Tanvir Hossain"]
