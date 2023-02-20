import logging

from aiogram import Bot

from cherino.config import CONFIG
from cherino.dispatcher import dp
from cherino.scheduler import Scheduler


def main():
    logging.basicConfig(level=logging.INFO)
    scheduler = Scheduler()
    bot = Bot(CONFIG.token, parse_mode="HTML")
    dp.run_polling(bot, scheduler=scheduler)


if __name__ == "__main__":
    main()
