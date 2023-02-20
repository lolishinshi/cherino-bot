from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

from cherino.filters import IsAdmin
from cherino import crud


router = Router()


class SettingState(StatesGroup):
    add_question = State()


class SettingsCallback(CallbackData, prefix="settings"):
    action: str


def settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="添加入群问题", callback_data=SettingsCallback(action="add_question").pack()
    )
    builder.button(text="完成", callback_data=SettingsCallback(action="finish").pack())
    builder.adjust(1, repeat=True)
    return builder.as_markup()


@router.message(Command("settings"), IsAdmin())
async def settings(message: Message):
    """
    打开全局设置
    """
    keyboard = settings_keyboard()
    await message.reply("同志，欢迎来到设置页面", reply_markup=keyboard)


@router.callback_query(SettingsCallback.filter(F.action == "finish"), IsAdmin())
async def finish(callback: CallbackQuery, state: FSMContext):
    """
    完成设置
    """
    await state.clear()
    await callback.message.delete()


@router.callback_query(SettingsCallback.filter(F.action == "add_question"), IsAdmin())
async def add_question(callback: CallbackQuery, state: FSMContext):
    """
    添加入群问题
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="返回", callback_data=SettingsCallback(action="backward").pack())
    await callback.message.edit_text(
        "请回复需要添加的问题，格式如下：\n问题描述\n正确答案\n错误答案1\n错误答案2", reply_markup=builder.as_markup()
    )
    await state.set_state(SettingState.add_question)
    await state.update_data()


@router.callback_query(SettingsCallback.filter(F.action == "backward"), IsAdmin())
async def backward(callback: CallbackQuery, state: FSMContext):
    """
    返回设置页面
    """
    keyboard = settings_keyboard()
    await state.clear()
    await callback.message.edit_text("同志，欢迎来到设置页面", reply_markup=keyboard)


@router.message(SettingState.add_question, IsAdmin())
async def process_add_question(message: Message, state: FSMContext):
    """
    记录回复的入群问题
    """
    if message.photo:
        image, text = message.photo[-1].file_id, message.caption
    else:
        image, text = None, message.text

    question, *answers = text.splitlines()
    crud.auth.add_question(message.chat.id, question, answers, image)

    builder = InlineKeyboardBuilder()
    builder.button(text="返回", callback_data=SettingsCallback(action="backward").pack())
    await message.reply("已添加，你可以选择继续添加或者点击返回", reply_markup=builder.as_markup())
    await message.delete()

