from aiogram import Router, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from loguru import logger

from cherino.filters import IsAdmin
from cherino import crud

router = Router()


@router.message(Command(commands=["/ban"]), IsAdmin())
async def ban(message: Message, bot: Bot, command: CommandObject):
    """
    封禁用户，并删除该用户所有消息
    """
    if not message.reply_to_message:
        return

    user = message.reply_to_message.from_user
    reason = command.args

    try:
        crud.ban(user.id, message.chat.id, reason)
        await bot.ban_chat_member(message.chat.id, user.id, revoke_messages=True)
        await message.reply("已肃清用户: {}\n理由: {}".format(user.mention_html(), reason))
    except Exception as e:
        logger.warning("封禁用户失败：{}", e)
    finally:
        await message.delete()


@router.message(Command(commands=["/warn"]), IsAdmin())
async def warn(message: Message, bot: Bot, command: CommandObject):
    """
    警告用户，当警告次数达到上限时，自动封禁用户
    """
    if not message.reply_to_message:
        return

    user = message.reply_to_message.from_user
    reason = command.args

    try:
        warn_cnt = crud.warn(user.id, message.chat.id, reason)
        if warn_cnt < 3:
            await message.reply("用户 {} 已被警告 {}/3 次\n理由: {}".format(user.mention_html(), warn_cnt, reason))
        else:
            crud.ban(user.id, message.chat.id, reason)
            await bot.ban_chat_member(message.chat.id, user.id)
            await message.reply("用户 {} 警告次数达到上限，已被肃清".format(user.mention_html()))

        await message.reply_to_message.delete()
    except Exception as e:
        logger.warning("警告用户失败：{}", e)
    finally:
        await message.delete()


@router.message(Command(commands=["/forgive"]), IsAdmin())
async def forgive(message: Message, bot: Bot):
    pass
