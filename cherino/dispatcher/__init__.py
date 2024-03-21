from aiogram import Dispatcher
from aiogram_dialog import setup_dialogs

from cherino.crud.state import SqliteStorage
from cherino.dispatcher import admin, auth, normal, settings, question, spam
from cherino.recent_message import RecentMessageMiddleware

dp = Dispatcher(storage=SqliteStorage())
dp.include_routers(
    admin.router,
    auth.router,
    settings.router,
    normal.router,
    question.router,
    spam.router,
)
dp.message.outer_middleware.register(RecentMessageMiddleware())
setup_dialogs(dp)
