from aiogram import Router, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from cherino.filters import IsAdmin
from cherino import crud
from cherino import utils

router = Router()


class ReportCallback(CallbackData, prefix="report"):
    user: int
    reporter: int
    message: int
    action: str


@router.message(Command(commands=["ping"]))
async def ping(message: Message):
    await message.reply("pong")


@router.message(Command(commands=["ban"]), IsAdmin())
async def ban(message: Message, bot: Bot, command: CommandObject):
    """
    封禁用户，并删除该用户所有消息
    """
    if not message.reply_to_message:
        return

    user = message.reply_to_message.from_user
    reason = command.args

    try:
        crud.user.ban(user.id, message.chat.id, reason)
        await bot.ban_chat_member(message.chat.id, user.id, revoke_messages=True)
        await message.reply("已肃清用户: {}\n理由: {}".format(user.mention_html(), reason))
    except Exception as e:
        logger.warning("封禁用户失败：{}", e)
    finally:
        await message.delete()


@router.message(Command(commands=["warn"]), IsAdmin())
async def warn(message: Message, bot: Bot, command: CommandObject):
    """
    警告用户，当警告次数达到上限时，自动封禁用户
    """
    if not message.reply_to_message:
        return

    user = message.reply_to_message.from_user
    reason = command.args

    try:
        warn_cnt = crud.user.warn(user.id, message.chat.id, reason)
        if warn_cnt < 3:
            await message.reply(
                "用户 {} 已被警告 {}/3 次\n理由: {}".format(
                    user.mention_html(), warn_cnt, reason
                )
            )
        else:
            crud.user.ban(user.id, message.chat.id, reason)
            await bot.ban_chat_member(message.chat.id, user.id)
            await message.reply("用户 {} 警告次数达到上限，已被肃清".format(user.mention_html()))

        await message.reply_to_message.delete()
    except Exception as e:
        logger.warning("警告用户失败：{}", e)
    finally:
        await message.delete()


@router.message(Command(commands=["reward"]), IsAdmin())
async def reward(message: Message, bot: Bot):
    pass


@router.message(Command(commands=["report"]))
async def report(message: Message, bot: Bot, command: CommandObject):
    """
    举报用户
    """
    if not message.reply_to_message:
        return

    user = message.reply_to_message.from_user
    reason = command.args

    builder = InlineKeyboardBuilder()
    for text, data in [("警告", "warn"), ("封禁", "ban"), ("举报", "report")]:
        builder.button(
            text=text,
            callback_data=ReportCallback(
                user=user.id,
                reporter=message.from_user.id,
                action=data,
                message=message.reply_to_message.message_id,
            ).pack(),
        )
    builder.adjust(2, 1)

    mention_admin = "".join(await utils.user.get_admin_mention(message.chat.id, bot))

    try:
        mention_user = user.id
        mention_reporter = message.from_user.id
        text = "{}用户：{}\n举报人：{}\n理由:{}".format(
            mention_admin, mention_user, mention_reporter, reason
        )
        await message.reply_to_message.reply(text, reply_markup=builder.as_markup())
    except Exception as e:
        logger.warning("举报用户失败：{}", e)


@router.callback_query(ReportCallback.filter(), IsAdmin())
async def report_callback(query: CallbackQuery, callback_data: ReportCallback):
    """
    处理举报回调
    """
    if callback_data.action == "ban":
        crud.user.ban(callback_data.user, query.message.chat.id, "举报")
        await query.message.chat.ban(callback_data.user)
        await query.message.edit_text(
            "已肃清用户: {}\n理由: {}".format(callback_data.user, "举报")
        )
    elif callback_data.action == "warn":
        warn_cnt = crud.user.warn(callback_data.user, query.message.chat.id, "举报")
        if warn_cnt < 3:
            await query.message.edit_text(
                "用户 {} 已被警告 {}/3 次\n理由: {}".format(callback_data.user, warn_cnt, "举报")
            )
        else:
            crud.user.ban(callback_data.user, query.message.chat.id, "举报")
            await query.message.chat.ban(callback_data.user)
            await query.message.edit_text(
                "用户 {} 警告次数达到上限，已被肃清".format(callback_data.user)
            )
    elif callback_data.action == "cancel":
        await query.message.delete()
