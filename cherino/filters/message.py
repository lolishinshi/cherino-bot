import re
from aiogram import Bot
from aiogram.filters import Filter
from aiogram.types import Message


class HasLink(Filter):
    """
    判断消息是否含有链接
    """

    MENTION_REGEX = re.compile("@[a-z0-9_]+")

    async def __call__(self, message: Message, bot: Bot) -> bool:
        if "http://" in message.text:
            return True
        if HasLink.MENTION_REGEX.search(message.text):
            return True
        return False
