from __future__ import annotations

import asyncio
import logging
from turtle import color
from typing import TYPE_CHECKING

import discord
from discord import Color, app_commands
from discord.app_commands import AppCommandChannel
from discord.ext import commands

from cogs.owner import OwnerCog
from cogs.watcher import WatcherCog

from .base import PageView, View

if TYPE_CHECKING:
    from bot import MidairBot

log = logging.getLogger(__name__)


class ServerListCog(commands.Cog):
    def __init__(self, bot):
        self.bot: MidairBot = bot

    async def configure_server_list(self, guild_id: int) -> ConfigureServerListView:
        async with self.bot.pool.acquire() as conn:
            query = "SELECT guild_id, channel_id, message_id, title FROM server_list WHERE guild_id=$1;"
            server_list = await conn.fetchone(query, guild_id)
            exists: bool = bool(server_list)
            title: str | None = server_list["title"] if server_list else None
            channel_id: int | None = server_list["channel_id"] if server_list else None
            message_id: int | None = server_list["message_id"] if server_list else None
            embed = await self.create_embed(
                channel_id, message_id, title, exists=bool(server_list)
            )
            view = ConfigureServerListView(self, self.bot, exists=exists, embed=embed)
            return view

    async def delete_server_list(
        self,
        guild_id: int,
    ):
        async with self.bot.pool.acquire() as conn:
            row = await conn.fetchone(
                "SELECT channel_id, message_id FROM server_list WHERE guild_id = $1",
                (guild_id),
            )
            channel_id: int = row["channel_id"]
            message_id: int = row["message_id"]
            guild: discord.Guild | None = self.bot.get_guild(guild_id)
            if guild and channel_id and message_id:
                # delete the message
                channel = guild.get_channel(channel_id)
                if isinstance(channel, discord.TextChannel):
                    message: discord.PartialMessage = channel.get_partial_message(
                        message_id
                    )
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        log.warning(
                            f"[delete_server_list] Missing permissions to delete message {message_id} "
                            f"in channel {channel_id} for guild {message_id}"
                        )
                    except discord.NotFound:
                        log.warning(
                            f"[delete_server_list] Could not find {message_id} "
                            f"in channel {channel_id} for guild {message_id}, but it may still exist in discord"
                        )
                    except discord.HTTPException:
                        log.warning(
                            f"[delete_server_list] Ignoring HTTP exception when deleting message {message_id} "
                            f"in channel {channel_id} for guild {message_id} but it may still exist in discord"
                        )
            await conn.execute("DELETE FROM server_list WHERE guild_id = $1", guild_id)
            await conn.commit()

    async def create_embed(
        self,
        channel_id: int | None = None,
        message_id: int | None = None,
        title: str | None = None,
        *,
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
            embed_description = "Create a new Server List."
            embed.set_footer(
                text="Note: If you can't see the channel in the list, start typings its name."
            )
        embed.description = embed_description
        return embed


class ConfigureServerListView(PageView):
    def __init__(
        self, cog: ServerListCog, bot: MidairBot, *, exists: bool, embed: discord.Embed
    ):
        super().__init__(timeout=None, embed=embed)
        self.cog: ServerListCog = cog
        self.bot: MidairBot = bot
        self.exists: bool = exists
        if not exists:
            self.add_item(create_server_list_button(self.cog, self.bot))
            pass
        else:
            # self.add_item(edit_server_list_button(self.cog, self.bot)) TODO
            self.add_item(delete_server_list_button(self.cog, self.bot))

class CreateServerListView(View):
    cog: ServerListCog
    bot: MidairBot
    channel: AppCommandChannel | None
    name: str
    embed: discord.Embed

    def __init__(
        self,
        cog: ServerListCog,
        bot: MidairBot,
        channel: AppCommandChannel | None = None,
        message: discord.Message | None = None,
        name: str = "Midair 2 Public Server List",
    ):
        super().__init__(timeout=None)
        self.cog: ServerListCog = cog
        self.bot: MidairBot = bot
        self.channel: AppCommandChannel | None = channel
        self.message: discord.Message | None = message
        self.name: str = name
        self.embed: discord.Embed = self.create_current_settings_embed()
        self.prev_view: View | None
        self.prev_embed: discord.Embed | None

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
        await interaction.response.edit_message(
            view=self.prev_view, embed=self.prev_embed
        )

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
            if self.message:
                await cog.edit_server_list(
                    interaction.guild_id,
                    self.channel.id,
                    self.message.id,
                    server_list_embed,
                )
                return
            new_message: discord.Message | None = await cog.send_server_list(
                interaction.guild_id, self.channel.id, server_list_embed
            )
            if not new_message:
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
            followup_embed = discord.Embed(
                title="Server List Created!",
                description=f"Check it out here {new_message.jump_url}",
                color=discord.Color.green(),
            )
            embed = await self.cog.create_embed(
                self.channel.id, new_message.id, self.name, exists=True
            )
            await interaction.response.edit_message(
                embed=embed,
                view=ConfigureServerListView(
                    self.cog, self.bot, exists=True, embed=embed
                ),
            )
            await interaction.followup.send(embed=followup_embed, ephemeral=True)
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


class ServerListNameModal(discord.ui.Modal, title="Server List Name"):
    def __init__(self, view: CreateServerListView):
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


class create_server_list_button(discord.ui.Button[ConfigureServerListView]):
    cog: ServerListCog
    bot: MidairBot

    def __init__(self, cog: ServerListCog, bot: MidairBot, disabled: bool = False):
        super().__init__(
            label="Create", disabled=disabled, style=discord.ButtonStyle.primary
        )
        self.cog = cog
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        view = CreateServerListView(self.cog, self.bot)
        if self.view:
            view.prev_view = self.view
            view.embed = self.view.embed
        await interaction.response.edit_message(embed=view.embed, view=view)


class delete_server_list_button(discord.ui.Button[ConfigureServerListView]):
    bot: MidairBot
    cog: ServerListCog

    def __init__(self, cog: ServerListCog, bot: MidairBot, disabled: bool = False):
        super().__init__(
            label="Delete", disabled=disabled, style=discord.ButtonStyle.danger
        )
        self.cog = cog
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        assert interaction.guild_id
        await self.cog.delete_server_list(interaction.guild_id)
        embed: discord.Embed = await self.cog.create_embed(exists=False)
        await interaction.response.edit_message(
            embed=embed,
            view=ConfigureServerListView(self.cog, self.bot, exists=False, embed=embed),
        )


class edit_server_list_button(discord.ui.Button[ConfigureServerListView]):
    bot: MidairBot

    def __init__(self, cog: ServerListCog, bot: MidairBot, disabled: bool = False):
        super().__init__(label="Edit", disabled=disabled)
        self.cog = cog
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.delete_original_response()


async def setup(bot: MidairBot):
    await bot.add_cog(ServerListCog(bot))
