from aiogram import Dispatcher

from cherino.dispatcher import admin

dp = Dispatcher()
dp.include_routers(basic.router)
