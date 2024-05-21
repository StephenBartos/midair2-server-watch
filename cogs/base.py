from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from typing import Any

log = logging.getLogger(__name__)

class View(discord.ui.View):

    def __init__(self, timeout: float | None):
        super().__init__(timeout=timeout)

    async def on_error(
        self,
        interaction: discord.Interaction[discord.Client],
        error: Exception,
        item: discord.ui.Item[Any],
    ) -> None:
        if interaction.response.is_done():
            await interaction.followup.send(
                embed=discord.Embed(
                    description="Oops! Something went wrong ☹️",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        else:
            # fallback case that responds to the interaction, since there always needs to be a response
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="Oops! Something went wrong ☹️",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        await super().on_error(interaction, error, item)

    async def disable_buttons(self, interaction: discord.Interaction):
        for child in self.children:
            if type(child) == discord.ui.Button and not child.disabled:
                child.disabled = True
        if interaction.message is not None:
            await interaction.message.edit(view=self)


class PageView(View):
    def __init__(
        self,
        timeout: float | None = None,
        embed: discord.Embed | None = None,
        prev_view: PageView | None = None,
    ):
        super().__init__(timeout=timeout)
        self.embed: discord.Embed | None = embed
        self.prev_view: PageView | None = prev_view


class BackButton(discord.ui.Button[PageView]):
    def __init__(self):
        super().__init__(label="← Back")

    # @discord.ui.button(label="← Back")
    async def callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.view:
            await interaction.response.edit_message(
                view=self.view.prev_view,
                embed=self.view.prev_view.embed if self.prev_view else None,
            )
        else:
            await interaction.response.edit_message(view=None, embed=None)
