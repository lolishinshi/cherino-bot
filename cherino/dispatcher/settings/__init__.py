from aiogram import Router

from . import question, settings

router = Router()
router.include_routers(
    question.router,
    settings.router,
)
