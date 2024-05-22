import logging

import aiohttp
import asqlite
import discord
from discord.ext import commands

import config

initial_extensions = (
    "cogs.owner",
    "cogs.watcher",
    "cogs.serverlist",
    "cogs.notifier",
    "cogs.configure",
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

    async def on_guild_join(self, guild: discord.Guild) -> None:
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO guild (id) VALUES ($1) ON CONFLICT DO NOTHING",
                    guild.id,
                )
                log.info(f'[on_guild_join] Joined guild "{guild.name}" ({guild.id})')
            except:
                log.exception(
                    f"[on_guild_join] Failed to insert guild_id {guild.id} into the guild table"
                )
                await conn.rollback()

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("DELETE FROM guild WHERE id = $1", guild.id)
                log.info(
                    f'[on_guild_remove] Removed from guild "{guild.name}" ({guild.id})'
                )
            except:
                log.exception(
                    f"[on_guild_join] Failed to remove guild_id {guild.id} from the guild table"
                )
                await conn.rollback()

    async def setup_hook(self) -> None:
        self.pool = await asqlite.create_pool(f"{config.DB_NAME}.db")
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
