from aiogram import Router, F
from aiogram.types import Message, ContentType


router = Router()


@router.message(F.content_type == ContentType.LEFT_CHAT_MEMBER)
@router.message(F.content_type == ContentType.NEW_CHAT_MEMBERS)
async def on_user_join(message: Message):
    await message.delete()
