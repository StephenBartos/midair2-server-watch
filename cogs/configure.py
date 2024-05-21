from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from cogs.base import PageView
from cogs.serverlist import ConfigureServerListView, ServerListCog

if TYPE_CHECKING:
    from bot import MidairBot


class ConfigureCog(commands.Cog, name="configure"):
    def __init__(self, bot):
        self.bot: MidairBot = bot

    @app_commands.command(
        name="configure", description="Setup and configuration editor"
    )
    @app_commands.guild_only()
    async def configure(self, interaction: discord.Interaction):
        embed_description: str = "Configure the Server List or Server Notifier"
        embed = discord.Embed(
            title="Configure",
            description=embed_description,
            color=discord.Color.yellow(),
        )
        view = ConfigureView(self, self.bot, embed)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ConfigureView(PageView):
    def __init__(self, cog: ConfigureCog, bot: MidairBot, embed: discord.Embed):
        super().__init__(timeout=None)
        self.cog: ConfigureCog = cog
        self.bot: MidairBot = bot
        self.embed: discord.Embed = embed

    @discord.ui.button(label="Server List")
    async def server_list(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        assert interaction.guild_id
        cog: commands.Cog | None = self.bot.get_cog("ServerListCog")
        if not isinstance(cog, ServerListCog):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="Oops! This feature is disabled right now ☹️",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return
        view: ConfigureServerListView = await cog.configure_server_list(
            interaction.guild_id
        )
        embed: discord.Embed = view.embed
        view.prev_view = self
        view.prev_embed = self.embed
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Notifications")
    async def notifier(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        pass


async def setup(bot: MidairBot):
    await bot.add_cog(ConfigureCog(bot))
