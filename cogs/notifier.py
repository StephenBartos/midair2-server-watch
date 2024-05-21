from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from bot import MidairBot

log = logging.getLogger(__name__)


class NotifierCog(commands.Cog):
    def __init__(self, bot):
        self.bot: MidairBot = bot


async def setup(bot: MidairBot):
    await bot.add_cog(NotifierCog(bot))
