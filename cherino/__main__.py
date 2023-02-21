import asyncio
import logging

from aiogram import Bot

from cherino.config import CONFIG
from cherino.dispatcher import dp
from cherino.scheduler import Scheduler


async def main():
    logging.basicConfig(level=logging.INFO)
    scheduler = Scheduler()
    bot = Bot(CONFIG.token, parse_mode="HTML")
    await dp.start_polling(bot, scheduler=scheduler)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
