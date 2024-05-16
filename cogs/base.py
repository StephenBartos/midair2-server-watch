from __future__ import annotations

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from typing import Any


class View(discord.ui.View):
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
        return

    async def disable_buttons(self, interaction: discord.Interaction):
        for child in self.children:
            if type(child) == discord.ui.Button and not child.disabled:
                child.disabled = True
        if interaction.message is not None:
            await interaction.message.edit(view=self)
