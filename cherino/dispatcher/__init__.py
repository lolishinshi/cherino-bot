from aiogram import Dispatcher

from cherino.dispatcher import admin, auth, settings, normal, clean

dp = Dispatcher()
dp.include_routers(
    admin.router, auth.router, settings.router, normal.router, clean.router
)
