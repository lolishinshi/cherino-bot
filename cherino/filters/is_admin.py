from aiogram import Bot
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery

from cherino.utils import user


class IsAdmin(Filter):
    def __init__(self):
        pass

    async def __call__(self, message: Message | CallbackQuery, bot: Bot) -> bool:
        if isinstance(message, CallbackQuery):
            return message.from_user.id in await user.get_admin(message.message.chat.id, bot)
        elif isinstance(message, Message):
            return message.from_user.id in await user.get_admin(message.chat.id, bot)
        raise RuntimeError("Unreachable")
