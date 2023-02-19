from aiogram import Router, Bot
from aiogram.filters import Command, JOIN_TRANSITION, ChatMemberUpdatedFilter
from aiogram.types import Message, ChatMemberUpdated, ChatPermissions

router = Router()


@router.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    permisson = ChatPermissions()
    await bot.restrict_chat_member(event.chat.id, event.old_chat_member.user.id)
