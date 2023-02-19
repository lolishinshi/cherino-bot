import asyncio

import asyncache
from aiogram import Bot
from aiogram.utils import markdown, link
from cachetools import TTLCache

from cherino.database.models import User
from cherino.database import db


async def get_admin(chat_id: int, bot: Bot) -> list[int]:
    asyncio.create_task(update_admin(chat_id, bot))
    admins = User.select().where(User.group == chat_id, User.is_admin)
    return [admin.id for admin in admins]


async def get_admin_mention(chat_id: int, bot: Bot) -> list[str]:
    ids = await get_admin(chat_id, bot)
    links = [link.create_tg_link("user", id=id_) for id_ in ids]
    return [markdown.hide_link(lk) for lk in links]


@asyncache.cached(TTLCache(maxsize=128, ttl=600))
async def update_admin(chat_id: int, bot: Bot):
    admins = await bot.get_chat_administrators(chat_id)
    with db.atomic():
        for admin in admins:
            User.create(id=admin.user.id, group=chat_id, is_admin=True)
