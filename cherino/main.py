from aiogram import Bot

from cherino.config import CONFIG
from cherino.dispatcher import dp


def main():
    bot = Bot(CONFIG.token, parse_mode="HTML")
    dp.run_polling(bot)
