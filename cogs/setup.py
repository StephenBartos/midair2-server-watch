from __future__ import annotations

import asyncio
import logging
from turtle import color
from typing import TYPE_CHECKING

import discord
from discord import Color, app_commands
from discord.app_commands import AppCommandChannel
from discord.ext import commands

from cogs.admin import Admin
from cogs.watcher import WatcherCog

from .base import View

if TYPE_CHECKING:
    from bot import MidairBot

log = logging.getLogger(__name__)


class SetupCog(commands.GroupCog, name="setup"):
    def __init__(self, bot):
        self.bot: MidairBot = bot

    @app_commands.command(name="serverlist")
    async def setup_server_list(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        async with self.bot.pool.acquire() as conn:
            query = "SELECT guild_id, channel_id, message_id, title FROM server_list WHERE guild_id=$1;"
            server_list = await conn.fetchone(query, interaction.guild_id)
            exists: bool = bool(server_list)
            view = SetupView(self, self.bot, exists)
            channel_id: int | None = server_list["channel_id"] if server_list else None
            message_id: int | None = server_list["message_id"] if server_list else None
            title: str | None = server_list["title"] if server_list else None
            embed = await self.create_embed(
                channel_id, message_id, title, bool(server_list)
            )
            await interaction.response.send_message(
                embed=embed, view=view, ephemeral=True
            )

    async def create_server_list(self, guild_id: int):
        pass

    async def edit_server_list(self, guild_id: int):
        pass

    @app_commands.command(name="serverwatcher")
    async def setup_server_watcher(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id

    async def create_embed(
        self,
        channel_id: int | None,
        message_id: int | None,
        title: str | None,
        exists: bool,
    ):
        embed = discord.Embed(
            title="Server List Configurator",
            color=discord.Color.yellow(),
        )
        if exists:
            embed_description = "Edit or Delete the existing Server List"
            title_str = f"`{title}`" if title else "*None*"
            channel = self.bot.get_channel(channel_id) if channel_id else None
            channel_str = (
                f"{channel.jump_url}"
                if isinstance(channel, discord.TextChannel)
                else "*None*"
            )
            message = (
                channel.get_partial_message(message_id)
                if message_id and isinstance(channel, discord.TextChannel)
                else None
            )
            message_str = f"{message.jump_url}" if message else "*None*"
            embed.add_field(name="🪧 Title", value=title_str)
            embed.add_field(name="📺 Channel", value=channel_str)
            embed.add_field(name="✉️ Message", value=message_str)
        else:
            embed_description = "Create a new Server List"
        embed.description = embed_description
        return embed


class ServerListNameModal(discord.ui.Modal, title="Server List Name"):
    def __init__(self, view: CreateServerList):
        super().__init__(timeout=None)
        self.view = view

    name = discord.ui.TextInput(
        label="Enter the name of the Server List",
        placeholder="Type your name here...",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        self.view.name = self.name.value
        embed: discord.Embed = self.view.create_current_settings_embed()
        self.view.embed = embed
        await interaction.response.edit_message(embed=self.view.embed)


class CreateServerList(View):
    cog: SetupCog
    bot: MidairBot
    channel: AppCommandChannel | None
    name: str
    embed: discord.Embed

    def __init__(
        self,
        cog: SetupCog,
        bot: MidairBot,
        channel: AppCommandChannel | None = None,
        name: str = "Midair 2 Public Server List",
    ):
        super().__init__(timeout=None)
        self.cog = cog
        self.bot = bot
        self.channel = channel
        self.name = name
        self.embed = self.create_current_settings_embed()

    @discord.ui.button(label="Set Title", row=1)  # title = name
    async def set_name(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(ServerListNameModal(self))

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Select the channel you want it to be posted in...",
        channel_types=[discord.ChannelType.text],
        min_values=1,
        max_values=1,
        row=2,
    )
    async def select_channel(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ):
        assert len(select.values) == 1
        assert isinstance(select.values[0], AppCommandChannel)
        self.channel = select.values[0]
        embed: discord.Embed = self.create_current_settings_embed()
        for child in self.children:
            if (
                isinstance(child, discord.ui.Button)
                and child.label
                and child.label == "Submit"
            ):
                child.disabled = False
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="← Back", row=3)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(
        label="Submit", row=3, style=discord.ButtonStyle.primary, disabled=True
    )
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert interaction.guild
        assert interaction.guild_id
        if not self.channel:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="P️lease select a channel to post in!",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return
        try:
            cog: commands.Cog | None = self.bot.get_cog("WatcherCog")
            if not isinstance(cog, WatcherCog):
                await interaction.response.send_message(
                    embed=discord.Embed(
                        description="Oops! This feature is disabled right now ☹️",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
                return
            server_list_embed: discord.Embed = cog.create_embed(self.name)
            message: discord.Message | None = await cog.send_server_list(
                interaction.guild_id, self.channel.id, server_list_embed
            )
            if not message:
                log.error(
                    f"[submit] Failed to send message in channel {self.channel.id} for guild {interaction.guild_id}"
                )
                await interaction.response.send_message(
                    embed=discord.Embed(
                        description="Oops! Something went wrong ☹️",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
                return
            embed = discord.Embed(
                title="Server List Created!",
                description=f"Check it out here {message.jump_url}",
                color=discord.Color.green(),
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except discord.Forbidden:
            log.exception(
                f"[submit] Missing permissions to post in guild {interaction.guild_id} inside channel {self.channel.id}"
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"I do not have permission to send messages in <#{self.channel.id}> ☹️",
                    color=discord.Color.red(),
                )
            )
        except discord.HTTPException:
            log.exception(
                f"[submit] Failed to post in guild {interaction.guild_id} inside channel {self.channel.id}"
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="Oops! Something went wrong when sending the message ☹️. Please try again...",
                    color=discord.Color.red(),
                )
            )

    def create_current_settings_embed(self) -> discord.Embed:
        description = "Configure the Server List"
        description += (
            "\n**Submit** will publish the Server List to the selected channel!"
        )
        embed = discord.Embed(
            title="⚙️ Create a Server List",
            description=description,
            color=discord.Color.yellow(),
        )
        channel_str = f"<#{self.channel.id}>" if self.channel else "*None selected*"
        embed.add_field(name="🪧 Current Title", value=f"`{self.name}`")
        embed.add_field(name="📺 Selected Channel", value=channel_str)
        return embed


class SetupView(View):
    cog: SetupCog
    bot: MidairBot
    exists: bool

    def __init__(self, cog: SetupCog, bot: MidairBot, exists: bool):
        super().__init__(timeout=None)
        self.cog = cog
        self.bot = bot
        self.exists = exists
        if not exists:
            self.add_item(create_server_list_button(self.cog, self.bot))
            pass
        else:
            self.add_item(edit_server_list_button(self.cog, self.bot))
            self.add_item(delete_server_list_button(self.cog, self.bot))

    @discord.ui.button(label="← Back")
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass


class create_server_list_button(discord.ui.Button[SetupView]):
    cog: SetupCog
    bot: MidairBot

    def __init__(self, cog: SetupCog, bot: MidairBot, disabled: bool = False):
        super().__init__(label="Create", disabled=disabled)
        self.cog = cog
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        view = CreateServerList(self.cog, self.bot)
        await interaction.response.edit_message(embed=view.embed, view=view)


class edit_server_list_button(discord.ui.Button[SetupView]):
    bot: MidairBot

    def __init__(self, cog: SetupCog, bot: MidairBot, disabled: bool = False):
        super().__init__(label="Edit", disabled=disabled)
        self.cog = cog
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        await interaction.delete_original_response()


class delete_server_list_button(discord.ui.Button[SetupView]):
    bot: MidairBot
    cog: SetupCog

    def __init__(self, cog: SetupCog, bot: MidairBot, disabled: bool = False):
        super().__init__(
            label="Delete", disabled=disabled, style=discord.ButtonStyle.danger
        )
        self.cog = cog
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM server_list WHERE guild_id = $1", interaction.guild_id
            )
            await conn.commit()
            await interaction.response.edit_message(
                view=SetupView(self.cog, self.bot, False)
            )


async def setup(bot: MidairBot):
    await bot.add_cog(SetupCog(bot))
