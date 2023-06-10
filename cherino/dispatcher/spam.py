from aiogram import F, Bot, Router
from aiogram.types import ContentType, Message
from aiogram.enums import ChatType
from loguru import logger

from cherino import crud
from cherino.filters import IsGroup, IsMember, HasLink, HasMedia

router = Router()


def allow_nonauth_media(message: Message) -> bool:
    return (
        crud.setting.get_setting(message.chat.id, "allow_nonauth_media", "yes") == "yes"
    )


@router.message(IsGroup(), ~IsMember(), HasMedia(), ~F.func(allow_nonauth_media))
async def on_nonauth_media(message: Message):
    """
    没有加入群组的用户，禁止发送媒体
    """
    logger.info("删除用户 {} 的 {} 类型消息", message.from_user.id, message.content_type)
    await message.delete()


@router.message(IsGroup(), ~IsMember(), HasLink(), ~F.func(allow_nonauth_media))
async def on_link(message: Message):
    """
    没有加入群组的用户，禁止发送链接
    """
    logger.info("删除用户 {} 包含链接的消息", message.from_user.id)
    await message.delete()
