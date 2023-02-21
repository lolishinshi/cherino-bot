from asyncio import sleep
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    ContentType,
    Message,
)
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from cherino import crud
from cherino.filters import MemberJoin
from cherino.scheduler import Scheduler
from cherino.utils.user import restrict_user

router = Router()


class UserAuthCallback(CallbackData, prefix="auth"):
    group: int
    question: int
    answer: int


class StartCallback(CallbackData, prefix="start"):
    group: int
    user: int


@router.message(F.content_type == ContentType.NEW_CHAT_MEMBERS, MemberJoin())
async def on_user_join(message: Message, bot: Bot, scheduler: Scheduler):
    """
    入群验证
    """
    logger.info("入群验证：{} - {}", message.chat.id, message.from_user.id)

    users = [user for user in message.new_chat_members if not user.is_bot]
    chat = message.chat

    try:
        if not crud.auth.get_question(message.chat.id):
            reply = await message.reply("本群未设置入群问题，默认不允许任何人加入，您将被踢出并封禁 1 分钟")
            await sleep(2)
            await message.delete()
            await reply.delete()
            for user in message.new_chat_members:
                await chat.ban(user.id, timedelta(seconds=60))
            return

        for user in message.new_chat_members:
            await restrict_user(chat.id, user.id, True, bot)
            scheduler.run_after(chat.ban(user.id, timedelta(days=1)), 60, job_id=f"auth:{message.chat.id}:{user.id}")
            crud.auth.add_pending_verify(chat.id, user.id)

        builder = InlineKeyboardBuilder()
        builder.button(text="前往审查", url=await create_start_link(bot, str(chat.id)))

        reply = await bot.send_message(
            chat.id,
            "新加入的同志，请在 60s 内点击下方按钮并完成审查".format(),
            reply_markup=builder.as_markup(),
        )

        scheduler.run_single(reply.delete(), 60, job_id="auth:delete-welcome")

    except Exception as e:
        logger.warning("入群提示失败: {}", e)


@router.message(CommandStart())
async def start(message: Message, bot: Bot, command: CommandObject):
    """
    处理通过 deep link 跳转过来的用户验证请求
    """
    try:
        chat_id = int(command.args)
        user = message.from_user

        question, answers = crud.auth.get_question(chat_id)
        builder = InlineKeyboardBuilder()
        for answer in answers:
            builder.button(
                text=answer.description,
                callback_data=UserAuthCallback(
                    group=chat_id, question=question.id, answer=answer.id
                ).pack(),
            )
        builder.adjust(1, repeat=True)

        pending_verify = crud.auth.get_pending_verify(chat_id, user.id)
        if not pending_verify:
            await message.reply("你当前没有待进行的审查")
            return
        if pending_verify.created_at + timedelta(seconds=60) < datetime.now():
            await message.reply("你当前的审查已经过期，请 24 小时后重新加入")
            pending_verify.delete_instance()
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
    query: CallbackQuery,
    callback_data: UserAuthCallback,
    scheduler: Scheduler,
    bot: Bot,
):
    """
    入群验证回调
    """

    try:
        pending_verify = crud.auth.get_pending_verify(
            callback_data.group, query.from_user.id
        )
        if (
            not pending_verify
            or pending_verify.created_at + timedelta(seconds=60) < datetime.now()
        ):
            await query.message.edit_text("你当前的审查已经过期")
            return
        pending_verify.delete_instance()

        success = crud.auth.add_answer(
            query.from_user.id, callback_data.question, callback_data.answer
        )
        if not success:
            await query.message.edit_text("很抱歉，回答错误，您将被移除本群。请 24 小时候再重试。")
            await sleep(2)
            # TODO: 随着失败次数增加，延长封禁时间
            await bot.ban_chat_member(
                callback_data.group, query.from_user.id, timedelta(hours=24)
            )
        else:
            await query.message.edit_text("欢迎你，同志！")
            await restrict_user(callback_data.group, query.from_user.id, False, bot)

        scheduler.cancel(f"auth:{callback_data.group}:{query.from_user.id}")
    except Exception as e:
        logger.error("入群验证回调失败: {}", e)

    if len(crud.auth.get_pending_verify(callback_data.group)) == 0:
        scheduler.run_single(lambda: None, 60, job_id="auth:delete-welcome")
