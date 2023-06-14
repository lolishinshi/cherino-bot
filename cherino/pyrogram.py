from typing import Generator

from pyrogram import Client
from pyrogram.types import ChatMember, User

from cherino.config import CONFIG


async def get_chat_members(chat_id: int) -> Generator[User, None, None]:
    if not CONFIG.api_id or not CONFIG.api_hash:
        return

    name = CONFIG.token.split(":")[0]
    async with Client(name, CONFIG.api_id, CONFIG.api_hash, bot_token=CONFIG.token) as client:
        async for member in client.get_chat_members(chat_id):
            member: ChatMember = member
            if member.user.is_bot:
                continue
            yield member.user
