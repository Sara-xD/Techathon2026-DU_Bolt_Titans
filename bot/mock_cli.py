"""Local console harness for the bot.

Runs the exact same command handlers a real Discord bot uses, so the whole
!status / !room / !usage / !alerts flow (and proactive alerts) can be demoed
and tested without a Discord application, token, or server. Set DISCORD_TOKEN
later and the identical handlers run for real (see bot.py).
"""
import asyncio
import sys

import backend_client as api
import handlers

PREFIX = "!"


def _force_utf8_console() -> None:
    """Make the console UTF-8 so emoji/em-dash replies don't crash the CLI.

    The bot's replies contain ✅ / ⚠️ / 🔴 / 🟡 / — . A native Windows console
    defaults to cp1252, which can't encode those, so print() raises
    UnicodeEncodeError. Reconfiguring stdout/stdin to UTF-8 fixes the local demo
    path. (The real Discord bot is unaffected -- Discord transmits UTF-8
    regardless of the host OS.)
    """
    for stream in (sys.stdout, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8")  # Python 3.7+
        except Exception:
            pass  # already UTF-8, or a stream that can't be reconfigured (e.g. a pipe)


_force_utf8_console()


async def _watch_alerts(seen: set[str], interval: int = 15):
    """Poll the backend and print newly-triggered alerts, like the real bot."""
    while True:
        try:
            active = await api.get_alerts()
            ids = {a["id"] for a in active}
            for a in active:
                if a["id"] not in seen:
                    seen.add(a["id"])
                    emoji = "🔴" if a["severity"] == "critical" else "🟡"
                    print(f"\n[proactive alert] {emoji} {a['message']}\n> ", end="", flush=True)
            seen.intersection_update(ids)
        except Exception:
            pass
        await asyncio.sleep(interval)


async def _dispatch(cmd: str) -> str | None:
    if cmd == f"{PREFIX}status":
        return await handlers.status_reply()
    if cmd.startswith(f"{PREFIX}room"):
        return await handlers.room_reply(cmd[len(PREFIX) + 4:].strip() or None)
    if cmd == f"{PREFIX}usage":
        return await handlers.usage_reply()
    if cmd == f"{PREFIX}alerts":
        return await handlers.alerts_reply()
    if cmd in (f"{PREFIX}help", "help"):
        return handlers.HELP_TEXT
    if cmd:
        return f"Unknown command. Try {PREFIX}status, {PREFIX}room <name>, {PREFIX}usage, {PREFIX}alerts, {PREFIX}help."
    return None


async def run():
    print("=" * 60)
    print("[bot] No DISCORD_TOKEN set -> running MOCK CLI mode.")
    print(f"[bot] Type commands as in Discord: {PREFIX}status | {PREFIX}room <name> | {PREFIX}usage | {PREFIX}alerts | {PREFIX}help | exit")
    print("=" * 60)

    seen: set[str] = set()
    watcher = asyncio.create_task(_watch_alerts(seen))
    loop = asyncio.get_event_loop()
    try:
        while True:
            try:
                line = await loop.run_in_executor(None, input, "> ")
            except EOFError:
                break  # piped input reached end
            cmd = line.strip()
            if cmd in ("exit", "quit"):
                break
            reply = await _dispatch(cmd)
            if reply is not None:
                print(reply)
    finally:
        watcher.cancel()
    print("[bot] mock CLI stopped.")
