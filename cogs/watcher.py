from __future__ import annotations

import asyncio
import logging
import sqlite3
from typing import TYPE_CHECKING

import aiohttp
import discord
from discord.ext import commands, tasks

import config

if TYPE_CHECKING:
    from bot import MidairBot

log = logging.getLogger(__name__)


class MidairServer:
    def __init__(
        self,
        name: str,
        max_players: int,
        players: int,
        map: str,
        serverAddress: str,
        version: str,
        addr: str,
        os: str,
        isPassworded: bool,
        gameVersion: str,
    ):
        self.name: str = name
        self.max_players: int = max_players
        self.players: int = players
        self.map: str = map
        self.server_address: str = serverAddress
        self.version: str = version
        self.addr: str = addr
        self.os: str = os
        self.is_passworded: bool = isPassworded
        self.game_version: str = gameVersion


class WatcherCog(commands.Cog):
    def __init__(self, bot):
        self.bot: MidairBot = bot
        # cache the list of servers, since there's no reason to persist them in the database currently
        self.midair_servers: list[MidairServer] = []
        self.midair_server_list_task.start()

    def cog_unload(self):
        self.midair_server_list_task.cancel()

    # @tasks.loop(minutes=1)
    @tasks.loop(seconds=10)
    async def midair_server_list_task(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(config.MIDAIR_SERVERS_API_URL) as resp:
                if resp.status != 200:
                    log.warning(
                        f"{config.MIDAIR_SERVERS_API_URL} HTTP response returned with status {resp.status}, skipping server list update."
                    )
                    return
                json_body = await resp.json()
                servers_json = json_body["servers"] if "servers" in json_body else []
                self.midair_servers: list[MidairServer] = (
                    [MidairServer(**j) for j in servers_json] if servers_json else []
                )
                self.midair_servers.sort(key=lambda x: x.players, reverse=True)
                await self.update_guild_server_lists()

    async def update_guild_server_lists(self):
        async with self.bot.pool.acquire() as conn:
            query = "SELECT guild_id, channel_id, message_Id, title  FROM server_list"
            try:
                coroutines = []
                res = await conn.execute(query)
                for row in await res.fetchall():
                    guild_id = row["guild_id"]
                    channel_id = row["channel_id"]
                    message_id = row["message_id"]
                    title = row["title"]
                    embed: discord.Embed = self.create_embed(title=title)
                    coroutines.append(
                        self.edit_server_list(guild_id, channel_id, message_id, embed)
                    )
                asyncio.gather(*coroutines)
            except sqlite3.Error:
                log.exception(f"[send_server_list] Failed to commit into the database")

    async def edit_server_list(
        self, guild_id: int, channel_id: int, message_id: int, embed: discord.Embed
    ):
        server_list_channel = self.bot.get_channel(channel_id)
        if not server_list_channel:
            log.error(
                f"[send_server_list] Failed to get channel {channel_id} in guild {guild_id}"
            )
            return None
        if isinstance(server_list_channel, discord.TextChannel):
            message: discord.PartialMessage = server_list_channel.get_partial_message(
                message_id
            )
            try:
                # Getting the cached PartialMessage to avoid emitting an API call
                await message.edit(embed=embed)
                return
            except discord.Forbidden:
                log.exception(
                    f"[edit_server_list] Missing permissions to edit message {message_id} in guild {guild_id}"
                )
                return
            except discord.HTTPException as e:
                if e.status == 404:
                    # message not found, so post a new one
                    log.warning(
                        f"[edit_server_list] message {message_id} not found in channel {channel_id} for guild {guild_id}, sending a new one"
                    )
                    await self.send_server_list(guild_id, channel_id, embed)
                else:
                    log.exception(
                        f"[edit_server_list] Ignoring HTTP exception when editing message {message_id} in channel {channel_id} for guild {guild_id}"
                    )
            """
            try:
                # Making an API call by fetching the message instead
                message = await server_list_channel.fetch_message(message_id)
                await message.edit(embed=embed)
            except discord.NotFound:
                log.exception(f'[edit_server_list] Failed to find message {message_id} in guild {guild_id}, sending a new one instead')
                await self.send_server_list(guild_id, channel_id, embed)
            except discord.Forbidden:
                log.exception(f'[edit_server_list] Missing permissions to fetch/edit message {message_id} in guild {guild_id}')
            except discord.HTTPException:
                log.exception(f'[edit_server_list] Failed to fetch/edit message {message_id} in guild {guild_id}, ignoring')
            """

    async def send_server_list(
        self, guild_id: int, channel_id: int, embed: discord.Embed
    ) -> discord.Message | None:
        server_list_channel = self.bot.get_channel(channel_id)
        if not server_list_channel:
            log.error(
                f"[send_server_list] Failed to get channel {channel_id} in guild {guild_id}"
            )
            return None
        if isinstance(server_list_channel, discord.TextChannel):
            message = await server_list_channel.send(embed=embed)
            async with self.bot.pool.acquire() as conn:
                try:
                    await conn.execute(
                        "INSERT INTO GUILD (guild_id) VALUES ($1) ON CONFLICT DO NOTHING",
                        guild_id,
                    )
                    query = """INSERT INTO server_list (guild_id, channel_id, message_id, title) VALUES ($1, $2, $3, $4)
                            ON CONFLICT(guild_id) DO UPDATE SET channel_id=$2, message_id=$3, title=$4"""
                    await conn.execute(
                        query, (guild_id, channel_id, message.id, embed.title)
                    )
                    await conn.commit()
                    return message
                except sqlite3.Error:
                    log.exception(
                        f"[send_server_list] Failed to commit into the database"
                    )
                    await conn.rollback()
                    return None

    def create_embed(self, title: str) -> discord.Embed:
        embed = discord.Embed(title=title, color=discord.Color.dark_embed())
        footer_text = "Only unlocked servers are shown."
        footer_text += "\nLast updated"
        embed.set_footer(text=footer_text)
        embed.timestamp = discord.utils.utcnow()
        for server in self.midair_servers:
            if server.game_version.lower() == "live":
                midair_app_id: int = 1231210  # "Midair 2 Playtest" Client
            else:
                midair_app_id: int = (
                    1231210  # TODO use correct app id for "Midair 2" client
                )
            if server.players < 0 or server.is_passworded:
                continue
            steam_connect_url = (
                f"steam://run/{midair_app_id}//+connect {server.server_address}"
            )
            embed.add_field(
                name="",
                value=(
                    f"[{server.players}/{server.max_players}] [{server.name}](https://midair2.gg/servers) - *{server.map}*"
                    if not server.is_passworded
                    else f"🔒{server.name}"
                ),
                inline=False,
            )
        if not self.midair_servers:
            embed.add_field(name="", value="*No servers to display...* ☹️", inline=False)
        return embed


async def setup(bot: MidairBot):
    await bot.add_cog(WatcherCog(bot))
