from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from cherino import crud
from cherino.filters import IsAdmin
from cherino.scheduler import Scheduler

from .settings import SettingsCallback, SettingState

router = Router()


@router.callback_query(SettingsCallback.filter(F.action == "add_question"), IsAdmin())
async def setting_add_question(callback: CallbackQuery, state: FSMContext):
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


@router.message(SettingState.add_question, IsAdmin())
async def process_add_question(message: Message, scheduler: Scheduler):
    """
    记录回复的入群问题
    """
    if message.photo:
        image, text = message.photo[-1].file_id, message.caption
    else:
        image, text = None, message.text

    question, *answers = text.splitlines()
    crud.auth.add_question(message.chat.id, question, answers, image)

    reply = await message.reply("已添加，你可以选择继续添加或者点击返回")

    scheduler.run_after(message.delete(), 5, str(message.message_id))
    scheduler.run_after(reply.delete(), 5, str(reply.message_id))


@router.callback_query(
    SettingsCallback.filter(F.action == "delete_question"), IsAdmin()
)
async def setting_delete_question(query: CallbackQuery, callback_data: SettingsCallback):
    """
    删除入群问题
    """
    try:
        if callback_data.data is not None:
            crud.auth.delete_question(query.message.chat.id, int(callback_data.data))

        question = crud.auth.get_all_questions(query.message.chat.id)
        builder = InlineKeyboardBuilder()
        for q in question:
            builder.button(
                text=q.description,
                callback_data=SettingsCallback(
                    action="delete_question", data=q.id
                ).pack(),
            )
        builder.button(text="返回", callback_data=SettingsCallback(action="backward").pack())
        builder.adjust(1, repeat=True)
        await query.message.edit_text(text="请选择需要删除的问题", reply_markup=builder.as_markup())
    except Exception as e:
        logger.warning("删除入群问题失败: {}", e)

