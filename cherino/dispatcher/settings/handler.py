from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import ManagedCheckboxAdapter, Button
from loguru import logger

from cherino.crud import auth
from cherino.crud.setting import Settings, set_setting, get_setting
from cherino.dispatcher.settings.state import SettingsSG
from cherino.utils.message import add_question_from_message


async def on_state_changed(
    event: CallbackQuery, checkbox: ManagedCheckboxAdapter, manager: DialogManager
):
    key = Settings(checkbox.widget.widget_id)
    value = checkbox.is_checked()
    logger.info("set {} = {}", key, value)
    set_setting(event.message.chat.id, key, value)


async def input_ban_time_handler(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    manager.show_mode = ShowMode.EDIT

    ban_time = message.text
    logger.info("set ban_time = {}", ban_time)
    set_setting(message.chat.id, Settings.BAN_TIME, ban_time)

    reply = await message.reply("已修改")
    scheduler = manager.middleware_data["scheduler"]
    scheduler.run_after(message.delete(), 5, str(message.message_id))
    scheduler.run_after(reply.delete(), 5, str(reply.message_id))

    await manager.switch_to(SettingsSG.MAIN)


async def input_add_question(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    manager.show_mode = ShowMode.EDIT
    add_question_from_message(message)

    reply = await message.reply("已添加，你可以选择继续添加或者点击返回")
    scheduler = manager.middleware_data["scheduler"]
    scheduler.run_after(message.delete(), 5, str(message.message_id))
    scheduler.run_after(reply.delete(), 5, str(reply.message_id))


async def on_click_ban_time(
    callback_query: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(SettingsSG.EDIT_BAN_TIME)


async def on_click_backward(
    callback_query: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(SettingsSG.MAIN)


async def on_click_cancel(
    callback_query: CallbackQuery, button: Button, manager: DialogManager
):
    await callback_query.message.delete()


async def on_dialog_start(data, manager: DialogManager):
    for key in Settings.__members__.values():
        checkbox = manager.find(key)
        if isinstance(checkbox, ManagedCheckboxAdapter):
            value = get_setting(manager.event.chat.id, key)
            checkbox.widget.set_widget_data(manager, value)


async def on_select_delete_question(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
):
    question = auth.get_all_questions(c.message.chat.id)[int(item_id) - 1]
    logger.info("删除问题：{}", question)
    auth.delete_question(c.message.chat.id, question.id)
