import operator

from aiogram import Router
from aiogram.filters.command import Command
from aiogram_dialog import (
    Window,
    StartMode,
    Dialog,
)
from aiogram_dialog.widgets.kbd import (
    Checkbox,
    Row,
    Cancel,
    SwitchTo,
    ScrollingGroup,
    Select,
)
from aiogram_dialog.widgets.text import Const, Format, Jinja

from cherino.dispatcher.settings.handler import *
from cherino.dispatcher.settings.getter import (
    setting_getter,
    question_getter,
    answer_stats_getter,
)
from cherino.dispatcher.settings.state import SettingsSG
from cherino.filters import AdminFilter

router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

dialog = Dialog(
    Window(
        Const("同志，欢迎来到设置页面"),
        Row(
            Checkbox(
                Const("允许加入 - 是"),
                Const("允许加入 - 否"),
                id=Settings.ALLOW_JOIN,
                on_state_changed=on_state_changed,
            ),
            Checkbox(
                Const("群内验证 - 是"),
                Const("群内验证 - 否"),
                id=Settings.AUTH_IN_GROUP,
                on_state_changed=on_state_changed,
            ),
        ),
        Row(
            Button(
                Format("封禁时长 - {ban_time}"),
                id=Settings.BAN_TIME,
                on_click=on_click_ban_time,
            ),
            Checkbox(
                Const(f"未入群用户发送媒体/链接 - 是"),
                Const(f"未入群用户发送媒体/链接 - 否"),
                id=Settings.ALLOW_NOAUTH_MEDIA,
                on_state_changed=on_state_changed,
            ),
        ),
        Row(
            SwitchTo(Const("添加问题"), id="add_question", state=SettingsSG.ADD_QUESTION),
            SwitchTo(
                Const("删除问题"), id="delete_question", state=SettingsSG.DEL_QUESTION
            ),
            SwitchTo(Const("修改问题"), id="edit_question", state=SettingsSG.EDIT_QUESTION),
        ),
        Row(
            Button(
                Const("链接题库"),
                id="link_question_group",
            ),
            Button(
                Const("删除题库"),
                id="delete_question_group",
            ),
        ),
        SwitchTo(Const("回答情况统计"), id="answer_stats", state=SettingsSG.ANSWER_STATS),
        Cancel(
            Const("完成"),
            on_click=on_click_cancel,
        ),
        state=SettingsSG.MAIN,
        getter=setting_getter,
    ),
    Window(
        Const("请回复新的封禁时长，如 1h、1d。超过 366d 或小于 30s 会视为永久封禁"),
        SwitchTo(Const("返回"), id="backward", state=SettingsSG.MAIN),
        MessageInput(input_ban_time_handler),
        state=SettingsSG.EDIT_BAN_TIME,
    ),
    Window(
        Const("请回复需要添加的问题，格式如下：\n问题描述\n正确答案\n错误答案1\n错误答案2"),
        SwitchTo(Const("返回"), id="backward", state=SettingsSG.MAIN),
        MessageInput(input_add_question),
        state=SettingsSG.ADD_QUESTION,
    ),
    Window(
        Const("请点击需要删除的问题"),
        ScrollingGroup(
            Select(
                Format("{item.description} - {item.correct_answer.description}"),
                id="s_questions",
                item_id_getter=operator.attrgetter("id"),
                items="questions",
                on_click=on_select_delete_question,
            ),
            id="select_question_to_delete",
            width=1,
            height=20,
        ),
        SwitchTo(Const("返回"), id="backward", state=SettingsSG.MAIN),
        getter=question_getter,
        state=SettingsSG.DEL_QUESTION,
    ),
    Window(
        Const("以下是当前群组的题库回答记录"),
        Jinja("<pre>{{answer_stats}}</pre>"),
        SwitchTo(Const("返回"), id="backward", state=SettingsSG.MAIN),
        getter=answer_stats_getter,
        state=SettingsSG.ANSWER_STATS,
    ),
    on_start=on_dialog_start,
)

router.include_router(dialog)


@router.message(Command("settings"))
async def cmd_settings(message: Message, dialog_manager: DialogManager):
    await message.delete()
    await dialog_manager.start(SettingsSG.MAIN, mode=StartMode.RESET_STACK)
