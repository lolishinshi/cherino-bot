from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from cherino import crud
from cherino.filters import IsAdmin

router = Router()


class SettingState(StatesGroup):
    add_question = State()


class SettingsCallback(CallbackData, prefix="settings"):
    action: str
    data: Optional[str]


def settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    allow_join = crud.setting.get_setting(chat_id, "allow_join", "yes")
    auth_type = crud.setting.get_setting(chat_id, "auth_type", "私聊")
    allow_nonauth_media = crud.setting.get_setting(
        chat_id, "allow_nonauth_media", "yes"
    )

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
        text="添加入群问题", callback_data=SettingsCallback(action="add_question").pack()
    )
    builder.button(
        text="删除入群问题", callback_data=SettingsCallback(action="delete_question").pack()
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
    t = crud.setting.get_setting(callback.message.chat.id, "allow_join", "yes")
    t = "no" if t == "yes" else "yes"
    crud.setting.set_setting(callback.message.chat.id, "allow_join", t)
    await open_settings(callback)


@router.callback_query(SettingsCallback.filter(F.action == "auth_type"), IsAdmin())
async def callback_auth_type(callback: CallbackQuery):
    """
    更改验证方式
    """
    t = crud.setting.get_setting(callback.message.chat.id, "auth_type", "私聊")
    t = "私聊" if t == "群内" else "群内"
    crud.setting.set_setting(callback.message.chat.id, "auth_type", t)
    await open_settings(callback)


@router.callback_query(
    SettingsCallback.filter(F.action == "allow_nonauth_media"), IsAdmin()
)
async def callback_allow_nonauth_media(callback: CallbackQuery):
    """
    更改是否允许未验证媒体
    """
    t = crud.setting.get_setting(callback.message.chat.id, "allow_nonauth_media", "yes")
    t = "no" if t == "yes" else "yes"
    crud.setting.set_setting(callback.message.chat.id, "allow_nonauth_media", t)
    await open_settings(callback)
