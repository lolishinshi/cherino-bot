from aiogram import Dispatcher

from cherino.dispatcher import admin, auth, normal, settings, question, spam

dp = Dispatcher()
dp.include_routers(
    admin.router,
    auth.router,
    settings.router,
    normal.router,
    question.router,
    spam.router,
)
