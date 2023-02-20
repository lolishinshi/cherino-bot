import asyncache
from aiogram import Bot
from aiogram.utils import markdown, link
from cachetools import TTLCache


@asyncache.cached(TTLCache(maxsize=128, ttl=600))
async def get_admin(chat_id: int, bot: Bot) -> list[int]:
    admins = await bot.get_chat_administrators(chat_id)
    return [admin.user.id for admin in admins if not admin.user.is_bot]


async def get_admin_mention(chat_id: int, bot: Bot) -> list[str]:
    ids = await get_admin(chat_id, bot)
    links = [link.create_tg_link("user", id=id_) for id_ in ids]
    return [markdown.hide_link(lk) for lk in links]
