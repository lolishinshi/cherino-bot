from aiogram import Bot
from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from cherino.utils.user import get_admin


class MemberJoin(Filter):
    """
    判断是否有成员加入，并且不是 bot 也不是被管理员邀请
    """

    async def __call__(self, message: Message, bot: Bot) -> bool:
        admins = await get_admin(message.chat.id, bot)
        users = []
        for user in message.new_chat_members:
            if not user.is_bot and message.from_user.id not in admins:
                users.append(user)
        return len(users) != 0


class IsAdmin(Filter):
    """
    判断消息来源是否是管理员
    """

    async def __call__(self, message: Message | CallbackQuery, bot: Bot) -> bool:
        if isinstance(message, CallbackQuery):
            return message.from_user.id in await get_admin(message.message.chat.id, bot)
        elif isinstance(message, Message):
            return message.from_user.id in await get_admin(message.chat.id, bot)
        raise RuntimeError("Unreachable")


class IsGroup(Filter):
    """
    判断消息来源是否是群组
    """

    async def __call__(self, message: Message | CallbackQuery, bot: Bot) -> bool:
        if isinstance(message, CallbackQuery):
            return message.message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        elif isinstance(message, Message):
            return message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        raise RuntimeError("Unreachable")
