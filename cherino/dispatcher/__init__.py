from aiogram import Dispatcher

from cherino.dispatcher import admin, auth, settings

dp = Dispatcher()
dp.include_routers(admin.router, auth.router, settings.router)
