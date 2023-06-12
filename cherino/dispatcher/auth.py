from asyncio import sleep
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, ContentType, InlineKeyboardMarkup, Message
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from pytimeparse import parse as parsetime

from cherino.crud import auth
from cherino.crud.setting import get_setting, Settings
from cherino.database.models import Question
from cherino.filters import MemberJoin
from cherino.scheduler import Scheduler
from cherino.utils.user import restrict_user

router = Router()


def can_join(message: Message) -> bool:
    return get_setting(message.chat.id, Settings.ALLOW_JOIN, "yes") == "yes"


def auth_in_group(message: Message) -> bool:
    return get_setting(message.chat.id, Settings.AUTH_TYPE, "私聊") == "群内"


def ban_time(message: Message) -> tuple[str, int]:
    t = get_setting(message.chat.id, Settings.BAN_TIME, "1h")
    return t, parsetime(t)


def get_question(chat_id: int, user_id: int) -> tuple[Question, InlineKeyboardMarkup]:
    question, answers = auth.get_question(chat_id)
    builder = InlineKeyboardBuilder()
    for answer in answers:
        builder.button(
            text=answer.description,
            callback_data=UserAuthCallback(
                group=chat_id, question=question.id, answer=answer.id, user=user_id
            ).pack(),
        )
    builder.adjust(1, repeat=True)
    return question, builder.as_markup()


class UserAuthCallback(CallbackData, prefix="auth"):
    group: int
    question: int
    answer: int
    user: int


class StartCallback(CallbackData, prefix="start"):
    group: int
    user: int


@router.message(
    F.content_type == ContentType.NEW_CHAT_MEMBERS, MemberJoin(), ~F.func(can_join)
)
async def on_user_join_deny(message: Message):
    """
    拒绝任何人加入
    """
    try:
        reply = await message.reply("本群不允许任何人加入，您将被踢出并封禁 1 分钟")
        await sleep(2)
        await message.delete()
        await reply.delete()
        for user in message.new_chat_members:
            if user.is_bot:
                continue
            await message.chat.ban(user.id, timedelta(seconds=60))
    except Exception as e:
        logger.warning("入群验证失败：{}", e)


@router.message(
    F.content_type == ContentType.NEW_CHAT_MEMBERS,
    MemberJoin(),
    F.func(can_join),
    ~F.func(auth_in_group),
)
async def on_user_join_private(message: Message, bot: Bot, scheduler: Scheduler):
    """
    入群验证 - 私聊
    """
    logger.info("入群验证：{} - {}", message.chat.id, message.from_user.id)

    users = [user for user in message.new_chat_members if not user.is_bot]
    chat = message.chat

    try:
        if not auth.get_question(message.chat.id):
            return

        for user in users:
            await restrict_user(chat.id, user.id, True, bot)
            # 超时后封禁用户
            scheduler.run_after(
                chat.ban(user.id, timedelta(hours=1)),
                60,
                job_id=f"auth:{message.chat.id}:{user.id}",
            )
            auth.add_pending_verify(chat.id, user.id)

        builder = InlineKeyboardBuilder()
        builder.button(text="前往审查", url=await create_start_link(bot, str(chat.id)))

        reply = await bot.send_message(
            chat.id,
            "新加入的同志，请在 60s 内点击下方按钮并完成审查".format(),
            reply_markup=builder.as_markup(),
        )

        # 准备在超时后删除验证消息
        scheduler.run_single(
            reply.delete(), 60, job_id=f"auth:delete-welcome:{chat.id}"
        )
        # 准备在超时后删除入群信息
        scheduler.run_after(
            message.delete(), 60, job_id=f"auth:delete-join:{chat.id}:{users[0].id}"
        )

    except Exception as e:
        logger.warning("入群提示失败: {}", e)


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    """
    处理通过 deep link 跳转过来的用户验证请求
    """
    try:
        chat_id = int(command.args)
        user = message.from_user

        question, answer_markup = get_question(chat_id, user.id)

        pending_verify = auth.get_pending_verify(chat_id, user.id)
        if not pending_verify:
            await message.reply("你当前没有待进行的审查")
            return
        if pending_verify.created_at + timedelta(seconds=60) < datetime.now():
            await message.reply("你当前的审查已经过期，请 1 小时后重新加入")
            pending_verify.delete_instance()
            return

        if question.image:
            await message.reply_photo(
                photo=question.image,
                caption=question.description,
                reply_markup=answer_markup,
            )
        else:
            await message.reply(
                text=question.description,
                reply_markup=answer_markup,
            )

    except Exception as e:
        logger.error("入群验证失败: {}", e)


@router.callback_query(UserAuthCallback.filter(), ~F.message.func(auth_in_group))
async def callback_auth_private(
    query: CallbackQuery,
    callback_data: UserAuthCallback,
    scheduler: Scheduler,
    bot: Bot,
):
    """
    入群验证回调
    """

    try:
        pending_verify = auth.get_pending_verify(
            callback_data.group, query.from_user.id
        )
        if (
            not pending_verify
            or pending_verify.created_at + timedelta(seconds=60) < datetime.now()
        ):
            await query.answer("你当前的审查已经过期")
            await query.message.delete()
            return
        pending_verify.delete_instance()

        success = auth.add_answer(
            query.from_user.id, callback_data.question, callback_data.answer
        )
        if not success:
            timestr, timeseconds = ban_time(query.message)
            await query.answer(f"很抱歉，回答错误，您将被移除本群。请 {timestr} 后再重试。")
            await bot.ban_chat_member(
                callback_data.group, query.from_user.id, timedelta(seconds=timeseconds)
            )
            # 验证失败，立即删除入群消息
            scheduler.trigger(
                f"auth:delete-join:{callback_data.group}:{query.from_user.id}"
            )
        else:
            await query.answer("欢迎你，同志！")
            await restrict_user(callback_data.group, query.from_user.id, False, bot)
            # 验证成功，取消删除入群消息
            scheduler.cancel(
                f"auth:delete-join:{callback_data.group}:{query.from_user.id}"
            )

        await query.message.delete()
        # 取消超时后封禁用用户的任务
        scheduler.cancel(f"auth:{callback_data.group}:{query.from_user.id}")
    except Exception as e:
        logger.error("入群验证回调失败: {}", e)

    # 如果当前已经没有待验证用户了，则可以立即删除验证消息
    if len(auth.get_pending_verify(callback_data.group)) == 0:
        scheduler.trigger(f"auth:delete-welcome:{callback_data.group}")


@router.message(
    F.content_type == ContentType.NEW_CHAT_MEMBERS,
    MemberJoin(),
    F.func(can_join),
    F.func(auth_in_group),
)
async def on_user_join_group(message: Message, bot: Bot, scheduler: Scheduler):
    """
    入群验证 - 群内
    """
    logger.info("入群验证：{} - {}", message.chat.id, message.from_user.id)

    users = [user for user in message.new_chat_members if not user.is_bot]
    chat = message.chat

    try:
        if not auth.get_question(chat.id):
            return

        for user in users:
            await restrict_user(chat.id, user.id, True, bot)

            question, answer_markup = get_question(chat.id, user.id)
            text = "新加入的同志，请在 60s 内回答下列问题\n{}".format(question.description)

            if question.image:
                reply = await message.reply_photo(
                    photo=question.image, caption=text, reply_markup=answer_markup
                )
            else:
                reply = await message.reply(text=text, reply_markup=answer_markup)

            # 超时后封禁用户
            scheduler.run_after(
                chat.ban(user.id, timedelta(hours=1)),
                60,
                job_id=f"auth:{chat.id}:{user.id}",
            )
            # 超时后删除验证消息
            scheduler.run_after(
                reply.delete(), 60, job_id=f"auth:delete-welcome:{chat.id}:{user.id}"
            )

        # 超时后删除入群信息
        # NOTE: 多位用户入群时此处只考虑第一位用户的认证状态
        scheduler.run_after(
            message.delete(), 60, job_id=f"auth:delete-join:{chat.id}:{users[0].id}"
        )

    except Exception as e:
        logger.warning("入群提示失败: {}", e)


@router.callback_query(UserAuthCallback.filter(), F.message.func(auth_in_group))
async def callback_auth_group(
    query: CallbackQuery,
    callback_data: UserAuthCallback,
    scheduler: Scheduler,
    bot: Bot,
):
    """
    入群验证回调
    """
    try:
        if query.from_user.id != callback_data.user:
            await query.answer("同志，请不要干扰我们工作！")
            return

        success = auth.add_answer(
            query.from_user.id, callback_data.question, callback_data.answer
        )
        if not success:
            timestr, timeseconds = ban_time(query.message)
            await query.answer(f"很抱歉，回答错误，您将被移除本群。请 {timestr} 后再重试。")
            await bot.ban_chat_member(
                callback_data.group, query.from_user.id, timedelta(seconds=timeseconds)
            )
            # 立即删除加入群组消息
            scheduler.trigger(
                f"auth:delete-join:{callback_data.group}:{query.from_user.id}"
            )
        else:
            await query.answer("欢迎你，新同志！")
            await restrict_user(callback_data.group, query.from_user.id, False, bot)
            # 取消删除加入群组消息
            scheduler.cancel(
                f"auth:delete-join:{callback_data.group}:{query.from_user.id}"
            )

        await query.message.delete()
        # 不管是否成功，都取消删除验证消息和封禁用户的任务
        scheduler.cancel(
            f"auth:delete-welcome:{query.message.chat.id}:{query.from_user.id}"
        )
        scheduler.cancel(f"auth:{callback_data.group}:{query.from_user.id}")
    except Exception as e:
        logger.error("入群验证回调失败: {}", e)
