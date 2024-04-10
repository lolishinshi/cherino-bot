from aiogram import F, Router, Bot
from aiogram.types import Message, User, Chat
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from cherino import crud
from cherino.config import CONFIG
from cherino.crud.setting import get_setting, Settings
from cherino.dispatcher.admin import ReportCallback
from cherino.utils.message import delete_all_message
from cherino.utils.nsfw import download_image, detect_nsfw
from cherino.filters import (
    IsGroup,
    IsMember,
    HasLink,
    HasMedia,
    IsSpam,
)
from cherino.utils.user import get_admin_mention
from cherino.recent_message import RecentMessage

router = Router()


def allow_nonauth_media(message: Message) -> bool:
    return get_setting(message.chat.id, Settings.ALLOW_NOAUTH_MEDIA)


def check_porn(message: Message) -> bool:
    return (
        get_setting(message.chat.id, Settings.CHECK_PORN)
        and CONFIG.nsfw_api is not None
    )


def aggressive_antispam(message: Message) -> bool:
    return get_setting(message.chat.id, Settings.AGGRESSIVE_ANTISPAM)


@router.message(IsGroup(), ~IsMember(), HasMedia(), ~F.func(allow_nonauth_media))
async def on_nonauth_media(message: Message):
    """
    没有加入群组的用户，禁止发送媒体
    """
    logger.info(
        "删除用户 {} 的 {} 类型消息", message.from_user.id, message.content_type
    )
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


@router.message(IsGroup(), HasLink(), F.func(aggressive_antispam))
@router.message(IsGroup(), F.via_bot, F.func(aggressive_antispam))
async def on_link(message: Message, bot: Bot, recent_message: RecentMessage):
    """
    检测广告
    """
    chat = message.chat
    user = message.from_user
    risk_level = await user_risk_level(user, chat)
    logger.info("用户 {} 风险等级: {}", user.id, risk_level)
    if risk_level >= 3:
        await delete_all_message(bot, chat.id, user.id, recent_message)
        await bot.ban_chat_member(chat.id, user.id, revoke_messages=True)
        mention_admin = "".join(await get_admin_mention(message.chat.id, bot))
        text = "{}已肃清用户: {}\n理由: {}".format(
            mention_admin, user.mention_html(str(user.id)), "疑似 spam"
        )
        await bot.send_message(chat.id, text)


@router.message(IsGroup(), HasMedia(), F.func(check_porn))
async def on_porn_check(message: Message, bot: Bot, recent_message: RecentMessage):
    """
    检测三次元色情内容
    """
    chat = message.chat
    user = message.from_user

    # TODO: 应该写成 filter
    # 获取图片为 porn 的可能性
    photo = await download_image(bot, message)
    nsfw_result = await detect_nsfw(photo)
    porn_level = nsfw_result["porn"]
    if porn_level < 0.7:
        return

    # 计算用户风险等级
    risk_level = await user_risk_level(user, chat)

    logger.info("用户 {} 风险等级: {}，色情等级：{}", user.id, risk_level, porn_level)

    # 根据风险等级和图片置信度，决定如何处理
    if porn_level >= 0.8 and risk_level >= 3:
        await delete_all_message(bot, chat.id, user.id, recent_message)
        await bot.ban_chat_member(chat.id, user.id, revoke_messages=True)
        mention_admin = "".join(await get_admin_mention(message.chat.id, bot))
        text = "{}已肃清用户: {}\n理由: {}".format(
            mention_admin, user.mention_html(str(user.id)), "疑似真人色情 spam"
        )
        await bot.send_message(chat.id, text)
    else:
        await message.delete()
        mention_admin = "".join(await get_admin_mention(message.chat.id, bot))
        text = "{}已清除消息: {}\n理由: {}".format(
            mention_admin, message.message_id, "疑似真人色情"
        )
        await bot.send_message(chat.id, text)


async def user_risk_level(user: User, chat: Chat) -> int:
    # 计算用户风险等级
    risk_level = 0

    avatar = await user.get_profile_photos(limit=1)
    if avatar.total_count == 0:
        risk_level += 1

    max_user_id = crud.user.max_user_id()
    if user.id > max_user_id * 0.95:
        risk_level += 1
    if user.id > max_user_id * 0.99:
        risk_level += 1

    last_seen = crud.user.get_user_last_seen(user.id, chat.id)
    if last_seen is None:
        risk_level += 2
    elif last_seen.active_days < 3:
        risk_level += 1

    return risk_level
