"""Discord bot -- the boss's quick-access remote control.

Commands (prefix `!`):
  !status         summary of every room
  !room <name>    one room (drawing / work1 / work2)
  !usage          current power + today's energy
  !alerts         active anomalies
  !help           list commands

Plus: a background task that proactively posts new alerts to a channel.

All answers come from the shared backend (same data as the web dashboard) and
are reworded warmly by Gemini, with a graceful factual fallback.
"""
import os

from dotenv import load_dotenv

load_dotenv()  # load .env before importing modules that read env at import time

import discord
from discord.ext import commands, tasks

import backend_client as api
import formatters as fmt
from humanizer import humanize

ALERT_CHANNEL_ID = int(os.getenv("ALERT_CHANNEL_ID", "0") or "0")
ALERT_POLL_SECONDS = int(os.getenv("ALERT_POLL_SECONDS", "30") or "30")

intents = discord.Intents.default()
intents.message_content = True  # required for prefix commands
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Alert ids we've already announced, so we don't spam the channel.
_announced: set[str] = set()


@bot.event
async def on_ready():
    print(f"[bot] Logged in as {bot.user} -- watching the office.")
    if not alert_watcher.is_running():
        alert_watcher.start()


async def _reply_or_error(ctx, coro_facts, context):
    """Fetch facts, humanize, and reply -- with a clear message if backend is down."""
    try:
        facts = await coro_facts
    except Exception as exc:
        await ctx.send(f"⚠️ I couldn't reach the office backend right now. ({exc})")
        return
    message = await humanize(facts, context)
    await ctx.send(message)


@bot.command(name="status")
async def status(ctx):
    async def facts():
        rooms = await api.get_rooms()
        return fmt.format_status(rooms)
    await _reply_or_error(ctx, facts(), "overall office device status")


@bot.command(name="room")
async def room(ctx, *, name: str = ""):
    room_id = fmt.resolve_room(name) if name else None
    if room_id is None:
        await ctx.send("Which room? Try `!room drawing`, `!room work1`, or `!room work2`.")
        return

    async def facts():
        r = await api.get_room(room_id)
        return fmt.format_room(r)
    await _reply_or_error(ctx, facts(), f"status of {room_id}")


@bot.command(name="usage")
async def usage(ctx):
    async def facts():
        u = await api.get_usage()
        return fmt.format_usage(u)
    await _reply_or_error(ctx, facts(), "current power usage and today's energy")


@bot.command(name="alerts")
async def alerts(ctx):
    async def facts():
        a = await api.get_alerts()
        return fmt.format_alerts(a)
    await _reply_or_error(ctx, facts(), "active office alerts")


@bot.command(name="help")
async def help_cmd(ctx):
    await ctx.send(
        "**Office Energy Monitor bot** 👋\n"
        "• `!status` — how every room looks right now\n"
        "• `!room <name>` — a single room (`drawing`, `work1`, `work2`)\n"
        "• `!usage` — power draw now + today's energy\n"
        "• `!alerts` — anything left running it shouldn't be\n"
        "I read live from the same backend as the web dashboard."
    )


@tasks.loop(seconds=ALERT_POLL_SECONDS)
async def alert_watcher():
    """Announce newly-triggered alerts to the designated channel."""
    if not ALERT_CHANNEL_ID:
        return
    try:
        active = await api.get_alerts()
    except Exception:
        return

    active_ids = {a["id"] for a in active}
    new = [a for a in active if a["id"] not in _announced]
    # Forget alerts that have cleared, so they can re-announce if they recur.
    _announced.intersection_update(active_ids)

    if not new:
        return
    channel = bot.get_channel(ALERT_CHANNEL_ID)
    if channel is None:
        return
    for a in new:
        _announced.add(a["id"])
        facts = f"ALERT ({a['severity']}): {a['message']}"
        msg = await humanize(facts, "a proactive heads-up about a device left running")
        await channel.send(f"⚠️ {msg}")


@alert_watcher.before_loop
async def _before_watcher():
    await bot.wait_until_ready()


def main():
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token or token.startswith("your-"):
        raise SystemExit(
            "DISCORD_TOKEN is not set. Copy bot/.env.example to bot/.env and add your token."
        )
    bot.run(token)


if __name__ == "__main__":
    main()
