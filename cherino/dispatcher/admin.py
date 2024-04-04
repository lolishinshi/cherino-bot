from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from cherino import crud
from cherino.filters import AdminFilter, IsGroup
from cherino.recent_message import RecentMessage
from cherino.scheduler import Scheduler
from cherino.utils.message import delete_all_message
from cherino.utils.user import get_admin, get_admin_mention

router = Router()


class ReportCallback(CallbackData, prefix="report"):
    report_id: int
    message: int
    action: str


@router.message(Command("offtopic"), IsGroup(), AdminFilter())
async def cmd_offtopic(
    message: Message, bot: Bot, command: CommandObject, scheduler: Scheduler
):
    """
    提示离题，并删除前面 N 条消息
    """
    delete_msg_cnt = 10
    if command.args and command.args.isnumeric():
        delete_msg_cnt = int(command.args)

    reply = await bot.send_message(message.chat.id, "当前讨论内容已离题")
    scheduler.run_after(
        reply.delete(), 120, f"delete-reply:{message.chat.id}:{message.message_id}"
    )

    for i in range(delete_msg_cnt):
        try:
            await bot.delete_message(message.chat.id, message.message_id - i)
        except:
            pass


@router.message(Command("mute"), IsGroup(), AdminFilter())
async def cmd_mute(
    message: Message, bot: Bot, command: CommandObject, scheduler: Scheduler
):
    """
    将用户禁言 60 分钟以内
    """
    if not message.reply_to_message:
        return

    # TODO


@router.message(Command("ban"), IsGroup(), AdminFilter())
async def cmd_ban(
    message: Message,
    bot: Bot,
    command: CommandObject,
    scheduler: Scheduler,
    recent_message: RecentMessage,
):
    """
    封禁用户，并删除该用户最近消息
    """
    if not message.reply_to_message:
        return

    user = message.reply_to_message.from_user
    operator = message.from_user
    reason = command.args

    try:
        crud.user.ban(user.id, operator.id, message.chat.id, reason)
        await bot.ban_chat_member(message.chat.id, user.id, revoke_messages=True)
        reply = await message.reply(
            "已肃清用户: {}\n理由: {}".format(user.mention_html(), reason)
        )
        scheduler.run_after(
            reply.delete(), 30, f"delete-ban:{message.chat.id}:{message.message_id}"
        )
        await delete_all_message(bot, message.chat.id, user.id, recent_message)
    except Exception as e:
        logger.warning("封禁用户失败：{}", e)
    finally:
        await message.delete()


@router.message(Command("warn"), IsGroup(), AdminFilter())
async def cmd_warn(message: Message, bot: Bot, command: CommandObject):
    """
    警告用户，当警告次数达到上限时，自动封禁用户
    """
    if not message.reply_to_message:
        return

    user = message.reply_to_message.from_user
    operator = message.from_user
    reason = command.args

    if user.id in await get_admin(
        message.chat.id, bot, lambda x: x.can_delete_messages
    ):
        return

    try:
        warn_cnt = crud.user.warn(user.id, operator.id, message.chat.id, reason)
        if warn_cnt < 3:
            await message.reply(
                "用户 {} 已被警告 {}/3 次\n理由: {}".format(
                    user.mention_html(), warn_cnt, reason
                )
            )
        else:
            crud.user.ban(user.id, operator.id, message.chat.id, "警告次数达到上限")
            await bot.ban_chat_member(message.chat.id, user.id)
            await message.reply(
                "用户 {} 警告次数达到上限，已被肃清".format(user.mention_html())
            )

        await message.reply_to_message.delete()
    except Exception as e:
        logger.warning("警告用户失败：{}", e)
    finally:
        await message.delete()


@router.message(Command("report"), IsGroup())
async def cmd_report(message: Message, bot: Bot, command: CommandObject):
    """
    举报用户
    """
    if not message.reply_to_message:
        return

    user = message.reply_to_message.from_user
    operator = message.from_user
    reason = command.args

    if user.id in await get_admin(
        message.chat.id, bot, lambda x: x.can_delete_messages
    ):
        return

    try:
        # TODO: 失败后，回滚数据库
        report_id = crud.user.report(user.id, operator.id, message.chat.id, reason).id
        builder = InlineKeyboardBuilder()
        for text, data in [("警告", "warn"), ("封禁", "ban"), ("撤销", "cancel")]:
            builder.button(
                text=text,
                callback_data=ReportCallback(
                    report_id=report_id,
                    action=data,
                    message=message.reply_to_message.message_id,
                ).pack(),
            )
        builder.adjust(2, 1)

        mention_admin = "".join(await get_admin_mention(message.chat.id, bot))
        text = "{}用户: {}\n举报人: {}\n理由: {}".format(
            mention_admin, user.mention_html(str(user.id)), operator.id, reason
        )

        await message.reply_to_message.reply(text, reply_markup=builder.as_markup())
    except Exception as e:
        logger.warning("举报用户失败：{}", e)
    finally:
        await message.delete()


@router.callback_query(
    ReportCallback.filter(F.action == "ban"),
    IsGroup(),
    AdminFilter(),
)
async def callback_report_ban(
    query: CallbackQuery,
    bot: Bot,
    callback_data: ReportCallback,
    scheduler: Scheduler,
    recent_message: RecentMessage,
):
    """
    处理举报回调
    """
    report = crud.user.get_report(callback_data.report_id)

    try:
        crud.user.handle_report(callback_data.report_id, query.from_user.id, "ban")
        await query.message.chat.ban(report.user)
        await query.message.edit_text(
            "已肃清用户: {}\n理由: {}".format(report.user, report.reason)
        )
        scheduler.run_after(query.message.delete(), 10, f"{query.message.message_id}")
        await delete_all_message(
            bot, query.message.chat.id, report.user, recent_message
        )
    except Exception as e:
        logger.warning("处理举报回调失败：{}", e)


@router.callback_query(
    ReportCallback.filter(F.action == "warn"), IsGroup(), AdminFilter()
)
async def callback_report_warn(
    query: CallbackQuery, callback_data: ReportCallback, scheduler: Scheduler
):
    """
    处理举报回调
    """
    report = crud.user.get_report(callback_data.report_id)

    try:
        await query.message.chat.delete_message(callback_data.message)
        warn_cnt = crud.user.handle_report(
            callback_data.report_id, query.from_user.id, "warn"
        )
        if warn_cnt < 3:
            await query.message.edit_text(
                "用户 {} 已被警告 {}/3 次\n理由: {}".format(
                    report.user, warn_cnt, report.reason
                )
            )
        else:
            crud.user.ban(
                report.user,
                query.from_user.id,
                query.message.chat.id,
                "警告次数达到上限",
            )
            await query.message.chat.ban(report.user)
            await query.message.edit_text(
                "用户 {} 警告次数达到上限，已被肃清".format(report.user)
            )
        scheduler.run_after(query.message.delete(), 10, f"{query.message.message_id}")
    except Exception as e:
        logger.warning("处理举报回调失败：{}", e)


@router.callback_query(
    ReportCallback.filter(F.action == "cancel"), IsGroup(), AdminFilter()
)
async def callback_report_cancel(query: CallbackQuery):
    """
    处理举报回调
    """
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning("处理举报回调失败：{}", e)
