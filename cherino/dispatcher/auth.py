from datetime import timedelta
from asyncio import sleep

from aiogram import Router, Bot, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.filters.callback_data import CallbackData
from aiogram.types import ChatPermissions, CallbackQuery, ContentType, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.deep_linking import create_start_link
from loguru import logger

from cherino import crud
from cherino.scheduler import Scheduler

router = Router()


class UserAuthCallback(CallbackData, prefix="auth"):
    group: int
    question: int
    answer: int


class StartCallback(CallbackData, prefix="start"):
    group: int
    user: int


@router.message(F.content_type == ContentType.NEW_CHAT_MEMBERS, ~F.from_user.is_bot)
async def on_user_join(message: Message, bot: Bot, scheduler: Scheduler):
    """
    入群验证
    """
    chat, user = message.chat, message.from_user
    read_only = ChatPermissions(**{k: False for k in ChatPermissions().dict().keys()})

    link = await create_start_link(bot, str(chat.id))
    builder = InlineKeyboardBuilder()
    builder.button(text="前往审查", url=link)

    async def ban():
        await chat.ban(user.id, timedelta(days=1))

    try:
        await message.delete()

        if not crud.auth.get_question(message.chat.id):
            # 如果没有任何问题，直接通过
            return

        await chat.restrict(user.id, read_only)

        new_message = await bot.send_message(
            chat.id,
            "新加入的同志，请在 60s 内点击下方按钮并完成审查".format(),
            reply_markup=builder.as_markup(),
        )

        crud.auth.add_pending_verify(chat.id, user.id)
        scheduler.run_after(new_message.delete, 60, job_id="auth:delete-welcome")
        scheduler.run_after(ban, 60, job_id=f"auth:{message.chat.id}:{user.id}")
    except Exception as e:
        logger.warning("入群提示失败: {}", e)


@router.message(CommandStart())
async def start(message: Message, bot: Bot, command: CommandObject):
    """
    处理通过 deep link 跳转过来的用户验证请求
    """
    chat_id = int(command.args)
    user = message.from_user

    question, answers = crud.auth.get_question(message.chat.id)
    builder = InlineKeyboardBuilder()
    for answer in answers:
        builder.button(
            text=answer.description,
            callback_data=UserAuthCallback(
                group=chat_id, question=question.id, answer=answer.id
            ).pack(),
        )

    try:
        if not crud.auth.get_pending_verify(chat_id, user.id):
            await message.reply("你已经是我们可靠的同志了！")
            return

        if question.image:
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=question.image,
                caption=question.description,
                reply_markup=builder.as_markup(),
            )
        else:
            await bot.send_message(
                chat_id=message.chat.id,
                text=question.description,
                reply_markup=builder.as_markup(),
            )

    except Exception as e:
        logger.error("入群验证失败: {}", e)


@router.callback_query(UserAuthCallback.filter())
async def auth_callback(
    query: CallbackQuery, callback_data: UserAuthCallback, scheduler: Scheduler, bot: Bot
):
    """
    入群验证回调
    """
    read_write = ChatPermissions(**{k: True for k in ChatPermissions().dict().keys()})

    try:
        # 先删掉消息，防止手快多次点击
        await query.message.delete()

        success = crud.auth.add_answer(
            query.from_user.id, callback_data.question, callback_data.answer
        )
        if not success:
            await query.answer("很抱歉，回答错误，您将被移除本群。请 24 小时候再重试。")
            await sleep(2)
            # TODO: 随着失败次数增加，延长封禁时间
            await bot.ban_chat_member(callback_data.group, query.from_user.id, timedelta(hours=24))
        else:
            await query.answer("欢迎你，同志！")
            await bot.restrict_chat_member(callback_data.group, query.from_user.id, read_write)

        scheduler.cancel(f"auth:{callback_data.group}:{query.from_user.id}")
    except Exception as e:
        logger.error("入群验证回调失败: {}", e)
