import asyncache
from aiogram import Bot
from aiogram.utils import link, markdown
from aiogram.types import ChatPermissions
from cachetools import TTLCache


@asyncache.cached(TTLCache(maxsize=128, ttl=600))
async def get_admin(chat_id: int, bot: Bot) -> list[int]:
    admins = await bot.get_chat_administrators(chat_id)
    return [admin.user.id for admin in admins if not admin.user.is_bot]


async def get_admin_mention(chat_id: int, bot: Bot) -> list[str]:
    ids = await get_admin(chat_id, bot)
    links = [link.create_tg_link("user", id=id_) for id_ in ids]
    return [markdown.hide_link(lk) for lk in links]


async def restrict_user(chat_id: int, user_id: int, status: bool, bot: Bot):
    """
    限制用户，status 为 True 表示限制所有权限
    """
    read_only = ChatPermissions(**{k: not status for k in ChatPermissions().dict().keys()})
    await bot.restrict_chat_member(chat_id, user_id, read_only)
