import asyncio
import logging

from aiogram import Bot

from cherino.logging import setup_logging
from cherino.config import CONFIG
from cherino.dispatcher import dp
from cherino.scheduler import Scheduler


async def main():
    setup_logging()
    bot = Bot(CONFIG.token, parse_mode="HTML")
    # NOTE: 此处在 Scheduler 之前调用 Bot.set_current，以便 Scheduler 启动时能成功处理持久化存储中的任务
    Bot.set_current(bot)
    scheduler = Scheduler()
    await dp.start_polling(
        bot, scheduler=scheduler, allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
