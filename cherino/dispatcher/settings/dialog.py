from aiogram import Router, Bot
from aiogram.filters.command import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.types import Message, Chat, CallbackQuery
from aiogram_dialog import (
    Window,
    DialogManager,
    StartMode,
    Dialog,
    ChatEvent,
    DialogProtocol,
    ShowMode,
)
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Checkbox,
    Row,
    ManagedCheckboxAdapter,
    Cancel,
)
from aiogram_dialog.widgets.text import Const, Format
from loguru import logger

from cherino.crud.setting import set_setting, get_setting, Settings
from cherino.filters import AdminFilter

router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


class SettingsSG(StatesGroup):
    main = State()
    edit_ban_time = State()


async def on_state_changed(
    event: CallbackQuery, checkbox: ManagedCheckboxAdapter, manager: DialogManager
):
    key = Settings(checkbox.widget.widget_id)
    value = {
        Settings.ALLOW_JOIN: ["no", "yes"],
        Settings.AUTH_TYPE: ["私聊", "群内"],
        Settings.ALLOW_NOAUTH_MEDIA: ["no", "yes"],
    }[key][int(checkbox.is_checked())]
    logger.info("set {} = {}", key, value)
    set_setting(event.message.chat.id, key, value)


async def get_data(event_chat: Chat, **kwargs) -> dict:
    return {Settings.BAN_TIME: get_setting(event_chat.id, Settings.BAN_TIME)}


async def input_ban_time_handler(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    ban_time = message.text
    logger.info("set ban_time = {}", ban_time)
    set_setting(message.chat.id, Settings.BAN_TIME, ban_time)
    manager.show_mode = ShowMode.EDIT
    await message.delete()
    await manager.switch_to(SettingsSG.main)


async def on_click_ban_time(
    callback_query: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(SettingsSG.edit_ban_time)


async def on_click_backward(
    callback_query: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(SettingsSG.main)


async def on_click_cancel(
    callback_query: CallbackQuery, button: Button, manager: DialogManager
):
    await callback_query.message.delete()


async def on_dialog_start(data, manager: DialogManager):
    for key in Settings.__members__.values():
        checkbox = manager.find(key)
        checkbox.widget.set_widget_data(
            manager, get_setting(manager.event.chat.id, key) == "yes"
        )

    checkbox: ManagedCheckboxAdapter = manager.find(Settings.ALLOW_JOIN)
    checkbox.widget.set_widget_data(
        manager, get_setting(manager.event.chat.id, Settings.ALLOW_JOIN) == "yes"
    )


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
                Const("验证方式 - 群内"),
                Const("验证方式 - 私聊"),
                id=Settings.AUTH_TYPE,
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
            Button(
                Const("添加问题"),
                id="add_question",
            ),
            Button(
                Const("删除问题"),
                id="delete_question",
            ),
            Button(
                Const("修改问题"),
                id="edit_question",
            ),
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
        Cancel(
            Const("完成"),
            on_click=on_click_cancel,
        ),
        state=SettingsSG.main,
        getter=get_data,
    ),
    Window(
        Const("请回复新的封禁时长，如 1h、1d。超过 366d 或小于 30s 会视为永久封禁"),
        Button(
            Const("返回"),
            id="backward",
            on_click=on_click_backward,
        ),
        MessageInput(input_ban_time_handler),
        state=SettingsSG.edit_ban_time,
    ),
    on_start=on_dialog_start,
)

router.include_router(dialog)


@router.message(Command("new_settings"), AdminFilter())
async def cmd_settings(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(SettingsSG.main, mode=StartMode.RESET_STACK)
