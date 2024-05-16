import logging

import aiohttp
import asqlite
import discord
from discord.ext import commands

import config

initial_extensions = (
    "cogs.admin",
    "cogs.watcher",
    "cogs.setup",
)
log = logging.getLogger(__name__)


class MidairBot(commands.Bot):
    pool: asqlite.Pool

    def __init__(self, token: str):
        self.token = token
        allowed_mentions = discord.AllowedMentions(
            roles=True, everyone=False, users=True
        )
        intents = discord.Intents(
            messages=True,
            guilds=True,
        )
        super().__init__(
            command_prefix=commands.when_mentioned,
            allowed_mentions=allowed_mentions,
            intents=intents,
        )

    async def setup_hook(self) -> None:
        self.pool = await asqlite.create_pool(config.DB_NAME)
        self.session = aiohttp.ClientSession()
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception:
                log.exception(f"Failed to load extension {extension}")

    async def close(self):
        await self.pool.close()
        await super().close()

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()

        log.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def start(self) -> None:
        await super().start(self.token, reconnect=True)
