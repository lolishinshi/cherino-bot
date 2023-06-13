from aiogram import Router

from . import question, settings, dialog

router = Router()
router.include_routers(
    question.router,
    settings.router,
    dialog.router,
)
