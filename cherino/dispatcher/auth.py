from datetime import timedelta
from asyncio import sleep

from aiogram import Router, Bot, F
from aiogram.filters.callback_data import CallbackData
from aiogram.types import ChatPermissions, CallbackQuery, ContentType, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from cherino import crud
from cherino.scheduler import Scheduler

router = Router()


class UserAuthCallback(CallbackData, prefix="auth"):
    user: int
    question: int
    answer: int


@router.message(F.content_type == ContentType.NEW_CHAT_MEMBERS, ~F.from_user.is_bot)
async def on_user_join(message: Message, bot: Bot, scheduler: Scheduler):
    """
    入群验证
    """
    user = message.from_user
    read_only = ChatPermissions(**{k: False for k in ChatPermissions().dict().keys()})

    try:
        question, answers = crud.auth.get_question(message.chat.id)

        await message.chat.restrict(user.id, read_only)

        text = "{} 同志你好，请在 30s 内回答以下问题以确定您的身份：\n{}".format(
            user.mention_html(), question.description
        )
        builder = InlineKeyboardBuilder()
        for answer in answers:
            builder.button(
                text=answer.description,
                callback_data=UserAuthCallback(
                    user=user.id, question=question.id, answer=answer.id
                ).pack(),
            )

        if question.image:
            message = await bot.send_photo(
                chat_id=message.chat.id,
                photo=question.image,
                caption=text,
                reply_markup=builder.as_markup(),
            )
        else:
            message = await bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=builder.as_markup(),
            )

        async def ban():
            await message.chat.ban(user.id, timedelta(days=1))
            await message.delete()
        scheduler.run_after(ban, 30, job_id=f"auth:{message.chat.id}:{user.id}")

    except Exception as e:
        logger.error("入群验证失败: {}", e)


@router.callback_query(UserAuthCallback.filter())
async def auth_callback(
    query: CallbackQuery, callback_data: UserAuthCallback, scheduler: Scheduler
):
    """
    入群验证回调
    """

    if query.from_user.id != callback_data.user:
        await query.answer("同志，请不要干扰我们工作")
        return

    read_write = ChatPermissions(**{k: True for k in ChatPermissions().dict().keys()})

    try:
        success = crud.auth.add_answer(
            query.from_user.id, callback_data.question, callback_data.answer
        )
        # 先删掉消息，防止手快多次点击
        await query.message.delete()
        if not success:
            await query.answer("很抱歉，回答错误，您将被移除本群。请 24 小时候再重试。")
            await sleep(2)
            await query.message.chat.ban(query.from_user.id, timedelta(hours=24))
        else:
            await query.answer("欢迎你，同志！")
            await query.message.chat.restrict(query.from_user.id, read_write)
        scheduler.cancel(f"auth:{query.message.chat.id}:{query.from_user.id}")
    except Exception as e:
        logger.error("入群验证回调失败: {}", e)
