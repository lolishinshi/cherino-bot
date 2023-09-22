import asyncio
import logging

from aiogram import Bot

from cherino.logging import setup_logging
from cherino.config import CONFIG
from cherino.dispatcher import dp
from cherino.scheduler import Scheduler, TelegramMethodJob


async def main():
    setup_logging()
    bot = Bot(CONFIG.token, parse_mode="HTML")
    TelegramMethodJob.set_bot(bot)
    scheduler = Scheduler()
    await dp.start_polling(
        bot, scheduler=scheduler, allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
