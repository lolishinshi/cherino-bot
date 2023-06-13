from aiogram import Router

from . import question, dialog

router = Router()
router.include_routers(
    question.router,
    dialog.router,
)
