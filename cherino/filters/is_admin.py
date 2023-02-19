from aiogram import Bot
from aiogram.filters import Filter
from aiogram.types import Message

from cherino.utils import get_admin


class IsAdmin(Filter):
    def __init__(self):
        pass

    async def __call__(self, message: Message, bot: Bot) -> bool:
        return message.from_user.id in await get_admin(message.chat.id, bot)
