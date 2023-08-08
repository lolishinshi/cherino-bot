import re
from aiogram import Bot
from aiogram.filters import Filter
from aiogram.types import Message, ContentType


class HasLink(Filter):
    """
    判断消息是否含有链接
    """

    MENTION_REGEX = re.compile("@[a-z0-9_]+")

    async def __call__(self, message: Message) -> bool:
        if message.text and ("http://" in message.text or "https://" in message.text):
            return True
        if HasLink.MENTION_REGEX.search(message.text):
            return True
        return False


class HasMedia(Filter):
    """
    判断消息是否含有媒体
    """

    async def __call__(self, message: Message) -> bool:
        return message.content_type in [
            ContentType.PHOTO,
            ContentType.VIDEO,
            ContentType.ANIMATION,
            # ContentType.STICKER,
            ContentType.DOCUMENT,
        ]


class IsSpam(Filter):
    """
    判断消息是否是 spam
    """

    regex = re.compile("私聊|群发|签名")

    async def __call__(self, message: Message, bot: Bot) -> bool:
        if IsSpam.regex.search(message.text):
            return True
        user = message.from_user
        if IsSpam.regex.search(user.first_name):
            return True
        if IsSpam.regex.search(user.last_name or ""):
            return True
        return False


class IsInvalidBot(Filter):
    """
    判断消息是否是无效的 bot 指令
    """

    async def __call__(self, message: Message, bot: Bot) -> bool:
        if message.text in ["/challenge@Sakowbot", "/getgroupid@myidbot", "/best@crypko_bot"]:
            return True
        return False
