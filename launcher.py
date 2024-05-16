import asyncio
import contextlib
import logging
from logging.handlers import RotatingFileHandler

import discord

import config
from bot import MidairBot


@contextlib.contextmanager
def setup_logging():
    log = logging.getLogger()

    try:
        discord.utils.setup_logging()
        # __enter__
        max_bytes = 32 * 1024 * 1024  # 32 MiB
        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.WARNING)

        log.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            filename="bot.log",
            encoding="utf-8",
            mode="w",
            maxBytes=max_bytes,
            backupCount=3,
        )
        dt_fmt = "%Y-%m-%d %H:%M:%S"
        fmt = logging.Formatter(
            "[{asctime}] [{levelname:<7}] {name}: {message}", dt_fmt, style="{"
        )
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield
    finally:
        # __exit__
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


async def run_bot():
    async with MidairBot(config.TOKEN) as bot:
        await bot.start()


def main():
    with setup_logging():
        asyncio.run(run_bot())


if __name__ == "__main__":
    main()
