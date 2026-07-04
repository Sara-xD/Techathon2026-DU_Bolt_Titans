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
import handlers
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
    print(f"[bot] Logged in as {bot.user} -- watching the office.", flush=True)
    if not alert_watcher.is_running():
        alert_watcher.start()


# The Discord commands are thin wrappers around the shared handlers, so the
# real bot and the mock CLI produce identical replies.
@bot.command(name="status")
async def status(ctx):
    await ctx.send(await handlers.status_reply())


@bot.command(name="room")
async def room(ctx, *, name: str = ""):
    await ctx.send(await handlers.room_reply(name or None))


@bot.command(name="usage")
async def usage(ctx):
    await ctx.send(await handlers.usage_reply())


@bot.command(name="alerts")
async def alerts(ctx):
    await ctx.send(await handlers.alerts_reply())


@bot.command(name="help")
async def help_cmd(ctx):
    await ctx.send(handlers.HELP_TEXT)


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
        emoji = "🔴" if a["severity"] == "critical" else "🟡"
        msg = await humanize(
            a["message"],
            "a brief, professional heads-up that devices were left on after office hours",
        )
        await channel.send(f"{emoji} {msg}")


@alert_watcher.before_loop
async def _before_watcher():
    await bot.wait_until_ready()


def main():
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token or token.startswith("your-"):
        # No Discord token -> run the local mock CLI (same handlers, no Discord
        # account needed). Great for judges to test the bot instantly.
        import asyncio
        import mock_cli
        asyncio.run(mock_cli.run())
        return
    bot.run(token)


if __name__ == "__main__":
    main()
