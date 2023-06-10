from aiogram import F, Router
from aiogram.types import ContentType, Message

from cherino import crud
from cherino.filters import IsGroup, IsMember, HasLink

router = Router()


def allow_nonauth_media(message: Message) -> bool:
    return (
        crud.setting.get_setting(message.chat.id, "allow_nonauth_media", "yes") == "yes"
    )


@router.message(
    IsGroup(),
    ~IsMember(),
    (F.content_type == ContentType.PHOTO)
    | (F.content_type == ContentType.VIDEO)
    | (F.content_type == ContentType.ANIMATION)
    | (F.content_type == ContentType.STICKER),
    ~F.func(allow_nonauth_media),
)
async def on_nonauth_media(message: Message):
    """
    没有加入群组的用户，禁止发送媒体
    """
    await message.delete()


@router.message(IsGroup(), ~IsMember(), HasLink(), ~F.func(allow_nonauth_media))
async def on_link(message: Message):
    """
    没有加入群组的用户，禁止发送链接
    """
    await message.delete()
