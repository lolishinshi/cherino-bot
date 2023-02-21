from aiogram import Dispatcher

from cherino.dispatcher import admin, auth, normal, settings

dp = Dispatcher()
dp.include_routers(
    admin.router, auth.router, settings.router, normal.router
)
