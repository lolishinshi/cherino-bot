from aiogram import Dispatcher
from aiogram_dialog import setup_dialogs

from cherino.crud.state import SqliteStorage
from cherino.dispatcher import admin, auth, normal, settings, question, spam

dp = Dispatcher(storage=SqliteStorage())
dp.include_routers(
    admin.router,
    auth.router,
    settings.router,
    normal.router,
    question.router,
    spam.router,
)
setup_dialogs(dp)
