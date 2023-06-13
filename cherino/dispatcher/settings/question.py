from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from cherino import crud
from cherino.filters import IsAdmin
from cherino.scheduler import Scheduler
from cherino.utils.message import add_question_from_message
from cherino.utils.pager import AbstractPager, PagerCallback

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
        "请回复需要关联的群组 ID 或者需要添加的问题，格式如下：\n问题描述\n正确答案\n错误答案1\n错误答案2",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(SettingState.add_question)
    await state.update_data()


@router.message(SettingState.add_question, IsAdmin())
async def process_add_question(message: Message, scheduler: Scheduler, bot: Bot):
    """
    记录回复的入群问题
    """
    if message.text.strip().lstrip("-").isnumeric():
        group_id = int(message.text.strip())
        group = await bot.get_chat(group_id)
        crud.auth.add_group_question(message.chat.id, group.id)
    else:
        add_question_from_message(message)

    reply = await message.reply("已添加，你可以选择继续添加或者点击返回")

    scheduler.run_after(message.delete(), 5, str(message.message_id))
    scheduler.run_after(reply.delete(), 5, str(reply.message_id))


@router.callback_query(
    SettingsCallback.filter(F.action == "delete_question"), IsAdmin()
)
@router.callback_query(PagerCallback.filter(F.name == "delete_question"), IsAdmin())
class DeleteQuestionPager(AbstractPager):
    @property
    def text(self) -> str:
        return "请选择需要删除的问题"

    @property
    def name(self) -> str:
        return "delete_question"

    def get_page(self, page: int = 0) -> InlineKeyboardBuilder:
        callback_data = self.data["callback_data"]
        if isinstance(callback_data, SettingsCallback) and callback_data.data:
            crud.auth.delete_question(self.message.chat.id, int(callback_data.data))

        builder = InlineKeyboardBuilder()
        question = crud.auth.get_all_questions(self.message.chat.id)
        for q in question[page * 20 : (page + 1) * 20]:
            builder.button(
                text=f"{q.description} - {q.correct_answer.description}",
                callback_data=SettingsCallback(action="delete_question", data=q.id),
            )
        builder.button(
            text="返回", callback_data=SettingsCallback(action="backward").pack()
        )
        return builder


@router.callback_query(
    SettingsCallback.filter(F.action == "delete_question_group"), IsAdmin()
)
async def setting_delete_question_group(
    callback: CallbackQuery, bot: Bot, callback_data: SettingsCallback
):
    """
    删除一个问题组
    """
    if callback_data.data is not None:
        crud.auth.delete_question_group(
            callback.message.chat.id, int(callback_data.data)
        )

    builder = InlineKeyboardBuilder()
    groups = crud.auth.get_question_group(callback.message.chat.id)
    for g in groups:
        chat_name = str(g.questions)
        try:
            chat_name = (await bot.get_chat(g.questions)).full_name
        except:
            pass
        builder.button(
            text=chat_name,
            callback_data=SettingsCallback(
                action="delete_question_group", data=g.questions
            ),
        )
    builder.button(text="返回", callback_data=SettingsCallback(action="backward").pack())
    builder.adjust(1)
    await callback.message.edit_text(
        text="以下是当前群组关联的问题组，点击以删除", reply_markup=builder.as_markup()
    )


@router.callback_query(
    SettingsCallback.filter(F.action == "answer_statistics"), IsAdmin()
)
async def setting_answer_statistics(query: CallbackQuery):
    """
    回答情况统计
    """
    try:
        questions = crud.auth.get_answer_stats(query.message.chat.id)
        texts = []
        for q, total, correct in questions:
            texts.append(
                f"{correct / total * 100:.1f}% - {correct}/{total} - {q.description} - {q.correct_answer.description}"
            )
        text = "\n".join(texts)
        builder = InlineKeyboardBuilder()
        builder.button(
            text="返回", callback_data=SettingsCallback(action="backward").pack()
        )
        builder.adjust(1, repeat=True)
        await query.message.edit_text(
            text=f"以下为问题库 {query.message.chat.id} 的回答情况统计\n<pre>\n{text}\n</pre>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("查看回答情况统计失败: {}", e)
