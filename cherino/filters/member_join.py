from aiogram import Bot
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from cherino.utils.user import get_admin


class MemberJoin(Filter):
    def __init__(self):
        pass

    async def __call__(self, message: Message, bot: Bot) -> bool:
        admins = await get_admin(message.chat.id, bot)
        users = []
        for user in message.new_chat_members:
            if not user.is_bot and message.from_user.id not in admins:
                users.append(user)
        return len(users) != 0
