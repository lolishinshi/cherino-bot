from aiogram import Router, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loguru import logger

from cherino.filters import IsAdmin
from cherino import crud

router = Router()


@router.message(Command(commands=["/report"]))
async def report(message: Message, bot: Bot):
    """
    举报用户
    """
    if not message.reply_to_message:
        return

    user = message.reply_to_message.from_user

