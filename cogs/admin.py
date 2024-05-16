from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal, Optional

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from bot import MidairBot

log = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
        self,
        ctx: Context,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
    ) -> None:
        """
        Do not use this command frequently, as it could get the bot rate limited
        https://about.abstractumbra.dev/discord.py/2023/01/29/sync-command-example.html
        """
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException as e:
                log.warn(f"Caught exception trying to sync for guild: ${guild}, e: {e}")
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def setup(bot: MidairBot):
    await bot.add_cog(Admin(bot))
