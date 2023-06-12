from typing import Optional

from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from cherino.crud.setting import get_setting, set_setting, Settings
from cherino.filters import IsAdmin
from cherino.scheduler import Scheduler

router = Router()


class SettingState(StatesGroup):
    add_question = State()
    edit_ban_time = State()


class SettingsCallback(CallbackData, prefix="settings"):
    action: str
    data: Optional[str]


def settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    allow_join = get_setting(chat_id, Settings.ALLOW_JOIN, "yes")
    auth_type = get_setting(chat_id, Settings.AUTH_TYPE, "私聊")
    allow_nonauth_media = get_setting(chat_id, Settings.ALLOW_NOAUTH_MEDIA, "yes")
    ban_time = get_setting(chat_id, Settings.BAN_TIME, "1h")

    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"允许加入 - {allow_join}",
        callback_data=SettingsCallback(action="allow_join").pack(),
    )
    builder.button(
        text=f"验证方式 - {auth_type}",
        callback_data=SettingsCallback(action="auth_type").pack(),
    )
    builder.button(
        text=f"封禁时长 - {ban_time}",
        callback_data=SettingsCallback(action="ban_time").pack(),
    )
    builder.button(
        text="添加入群问题", callback_data=SettingsCallback(action="add_question").pack()
    )
    builder.button(
        text="删除入群问题", callback_data=SettingsCallback(action="delete_question").pack()
    )
    builder.button(
        text="回答情况统计", callback_data=SettingsCallback(action="answer_statistics").pack()
    )
    builder.button(
        text=f"未入群用户发送媒体/链接 - {allow_nonauth_media}",
        callback_data=SettingsCallback(action="allow_nonauth_media").pack(),
    )
    builder.button(text="完成", callback_data=SettingsCallback(action="finish").pack())
    builder.adjust(1, repeat=True)
    return builder.as_markup()


async def open_settings(callback: CallbackQuery):
    keyboard = settings_keyboard(callback.message.chat.id)
    await callback.message.edit_text("同志，欢迎来到设置页面", reply_markup=keyboard)


@router.message(Command("settings"), IsAdmin())
async def settings(message: Message):
    """
    打开全局设置
    """
    logger.info("打开全局设置: {}", message.chat.id)
    keyboard = settings_keyboard(message.chat.id)
    await message.reply("同志，欢迎来到设置页面", reply_markup=keyboard)


@router.callback_query(SettingsCallback.filter(F.action == "finish"), IsAdmin())
async def finish(callback: CallbackQuery, state: FSMContext):
    """
    完成设置
    """
    await state.clear()
    await callback.message.reply_to_message.delete()
    await callback.message.delete()


@router.callback_query(SettingsCallback.filter(F.action == "backward"), IsAdmin())
async def backward(callback: CallbackQuery, state: FSMContext):
    """
    返回设置页面
    """
    await state.clear()
    await open_settings(callback)


@router.callback_query(SettingsCallback.filter(F.action == "allow_join"), IsAdmin())
async def callback_allow_join(callback: CallbackQuery):
    """
    更改是否允许加入
    """
    t = get_setting(callback.message.chat.id, Settings.ALLOW_JOIN, "yes")
    t = "no" if t == "yes" else "yes"
    set_setting(callback.message.chat.id, Settings.ALLOW_JOIN, t)
    await open_settings(callback)


@router.callback_query(SettingsCallback.filter(F.action == "auth_type"), IsAdmin())
async def callback_auth_type(callback: CallbackQuery):
    """
    更改验证方式
    """
    t = get_setting(callback.message.chat.id, Settings.AUTH_TYPE, "私聊")
    t = "私聊" if t == "群内" else "群内"
    set_setting(callback.message.chat.id, Settings.AUTH_TYPE, t)
    await open_settings(callback)


@router.callback_query(
    SettingsCallback.filter(F.action == "allow_nonauth_media"), IsAdmin()
)
async def callback_allow_nonauth_media(callback: CallbackQuery):
    """
    更改是否允许未验证媒体
    """
    t = get_setting(callback.message.chat.id, Settings.ALLOW_NOAUTH_MEDIA, "yes")
    t = "no" if t == "yes" else "yes"
    set_setting(callback.message.chat.id, Settings.ALLOW_NOAUTH_MEDIA, t)
    await open_settings(callback)


@router.callback_query(SettingsCallback.filter(F.action == "ban_time"), IsAdmin())
async def callback_ban_time(callback: CallbackQuery, state: FSMContext):
    """
    更改封禁时长
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="返回", callback_data=SettingsCallback(action="backward").pack())
    await callback.message.edit_text(
        "请回复封禁时长，如 1h、1d，超过 366d 或小于 30s 会视为永久封禁",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(SettingState.edit_ban_time)
    await state.update_data()


@router.message(SettingState.edit_ban_time, IsAdmin())
async def process_edit_ban_time(message: Message, scheduler: Scheduler):
    """
    修改封禁时长
    """
    set_setting(message.chat.id, Settings.BAN_TIME, message.text.strip())
    reply = await message.reply("已修改，你可以选择重新修改或者点击返回")
    scheduler.run_after(message.delete(), 5, str(message.message_id))
    scheduler.run_after(reply.delete(), 5, str(reply.message_id))
