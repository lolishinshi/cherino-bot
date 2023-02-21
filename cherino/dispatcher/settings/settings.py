from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from cherino.filters import IsAdmin

router = Router()


class SettingState(StatesGroup):
    add_question = State()


class SettingsCallback(CallbackData, prefix="settings"):
    action: str
    data: Optional[str]


def settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="添加入群问题", callback_data=SettingsCallback(action="add_question").pack()
    )
    builder.button(
        text="删除入群问题", callback_data=SettingsCallback(action="delete_question").pack()
    )
    builder.button(text="完成", callback_data=SettingsCallback(action="finish").pack())
    builder.adjust(1, repeat=True)
    return builder.as_markup()


@router.message(Command("settings"), IsAdmin())
async def settings(message: Message):
    """
    打开全局设置
    """
    logger.info("打开全局设置: {}", message.chat.id)
    keyboard = settings_keyboard()
    await message.reply("同志，欢迎来到设置页面", reply_markup=keyboard)


@router.callback_query(SettingsCallback.filter(F.action == "finish"), IsAdmin())
async def finish(callback: CallbackQuery, state: FSMContext):
    """
    完成设置
    """
    await state.clear()
    await callback.message.delete()


@router.callback_query(SettingsCallback.filter(F.action == "backward"), IsAdmin())
async def backward(callback: CallbackQuery, state: FSMContext):
    """
    返回设置页面
    """
    keyboard = settings_keyboard()
    await state.clear()
    await callback.message.edit_text("同志，欢迎来到设置页面", reply_markup=keyboard)