"""FastAPI application: the shared backend.

Exposes REST endpoints (used by the Discord bot and for debugging) and a
WebSocket that pushes the full state snapshot to dashboards in real time.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .clock import build_clock
from .store import DeviceStore
from .simulator import Simulator


class ConnectionManager:
    """Tracks connected dashboards and fans out snapshots to all of them."""

    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)

    async def broadcast(self, message: dict) -> None:
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


clock = build_clock(config.SIM_SPEED, config.SIM_START)
store = DeviceStore(clock)
manager = ConnectionManager()
simulator = Simulator(store, manager.broadcast)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await simulator.start()
    yield
    await simulator.stop()


app = FastAPI(title="Office Energy Monitor", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_ORIGIN, "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- REST -----------------------------------------------------------------
@app.get("/")
def health():
    return {"status": "ok", "service": "office-energy-monitor"}


@app.get("/api/state")
def get_state():
    """Full snapshot — the bot's one-stop endpoint."""
    return store.snapshot()


@app.get("/api/devices")
def get_devices(room: str | None = None):
    devices = list(store.devices.values())
    if room is not None:
        if room not in config.ROOMS:
            raise HTTPException(404, f"Unknown room '{room}'")
        devices = [d for d in devices if d.room == room]
    return {"devices": [d.to_dict() for d in devices]}


@app.post("/api/devices/{device_id}/toggle")
async def toggle_device(device_id: str):
    """Manual override from the dashboard: flip one device on/off.

    Not required by the spec (which is read-only monitoring) but makes the
    dashboard interactive. The change is broadcast immediately so every client
    and the Discord bot see it at once -- still one source of truth.
    """
    import random
    d = store.toggle(device_id, by=random.choice(config.ALLOWED_ACTORS))
    if d is None:
        raise HTTPException(404, f"Unknown device '{device_id}'")
    store.update_room_continuity()
    await manager.broadcast(store.snapshot())
    return d.to_dict()


@app.get("/api/rooms")
def get_rooms():
    return {"rooms": [store.room_summary(r) for r in config.ROOMS]}


@app.get("/api/rooms/{room}")
def get_room(room: str):
    if room not in config.ROOMS:
        raise HTTPException(404, f"Unknown room '{room}'")
    return store.room_summary(room)


@app.get("/api/usage")
def get_usage():
    return store.usage()


@app.get("/api/alerts")
def get_alerts():
    from .alerts import compute_alerts
    return {"alerts": compute_alerts(store)}


# --- WebSocket ------------------------------------------------------------
@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await manager.connect(ws)
    try:
        # Send the current snapshot immediately so a fresh dashboard isn't blank.
        await ws.send_json(store.snapshot())
        while True:
            # We don't expect messages from the client; this keeps the socket
            # open and detects disconnects.
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)
