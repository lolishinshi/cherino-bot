from aiogram import Dispatcher

from cherino.dispatcher import admin, auth, normal, settings, add_question

dp = Dispatcher()
dp.include_routers(admin.router, auth.router, settings.router, normal.router, add_question.router)
