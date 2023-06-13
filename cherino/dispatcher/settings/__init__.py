from aiogram import Router

from . import dialog

router = Router()
router.include_routers(
    dialog.router,
)
