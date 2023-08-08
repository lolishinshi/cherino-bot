from aiogram import F, Router, Bot
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from cherino import crud
from cherino.crud.setting import get_setting, Settings
from cherino.dispatcher.admin import ReportCallback
from cherino.filters import IsGroup, IsMember, HasLink, HasMedia, IsSpam, IsInvalidBot
from cherino.utils.user import get_admin_mention

router = Router()


def allow_nonauth_media(message: Message) -> bool:
    return get_setting(message.chat.id, Settings.ALLOW_NOAUTH_MEDIA)


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


@router.message(IsGroup(), ~IsMember(), IsSpam())
async def on_spam(message: Message, bot: Bot):
    """
    疑似 spam，报告管理员
    """
    user = message.from_user
    operator = bot
    reason = "疑似 spam"

    report_id = crud.user.report(user.id, operator.id, message.chat.id, reason).id
    builder = InlineKeyboardBuilder()
    for text, data in [("封禁", "ban"), ("撤销", "cancel")]:
        builder.button(
            text=text,
            callback_data=ReportCallback(
                report_id=report_id,
                action=data,
                message=message.message_id,
            ).pack(),
        )
    builder.adjust(2)

    mention_admin = "".join(await get_admin_mention(message.chat.id, bot))
    text = "{}用户: {}\n举报人: BOT\n理由: {}".format(
        mention_admin, user.mention_html(str(user.id)), reason
    )

    await message.reply(text, reply_markup=builder.as_markup())


@router.message(IsGroup(), IsInvalidBot())
async def on_invalid_bot_cmd(message: Message):
    await message.delete()
