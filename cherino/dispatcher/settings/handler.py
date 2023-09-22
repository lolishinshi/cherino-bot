from typing import Any
from datetime import timedelta

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import ManagedCheckbox, Button
from loguru import logger

from cherino.crud import auth
from cherino.crud.setting import Settings, set_setting, get_setting
from cherino.dispatcher.settings.state import SettingsSG
from cherino.utils.message import add_question_from_message


async def on_state_changed(
    event: CallbackQuery, checkbox: ManagedCheckbox, manager: DialogManager
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


async def input_add_question_group(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    manager.show_mode = ShowMode.EDIT
    group_id = int(message.text.strip())
    auth.add_group_question(message.chat.id, group_id)

    reply = await message.reply("已添加，你可以选择继续添加或者点击返回")
    scheduler = manager.middleware_data["scheduler"]
    scheduler.run_after(message.delete(), 5, str(message.message_id))
    scheduler.run_after(reply.delete(), 5, str(reply.message_id))


async def input_nothing_handler(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    await manager.done()


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
        if isinstance(checkbox, ManagedCheckbox):
            value = get_setting(manager.event.chat.id, key)
            checkbox.widget.set_widget_data(manager, value)


async def on_select_delete_question(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
):
    logger.info("删除问题：{}", item_id)
    auth.delete_question(c.message.chat.id, int(item_id))


async def on_click_confirm_purge(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    from cherino.pyrogram import get_chat_members

    bot: Bot = manager.middleware_data["bot"]
    async for user in get_chat_members(c.message.chat.id):
        _, correct = auth.get_user_answer_stats(c.message.chat.id, user.id)
        if correct == 0:
            await bot.ban_chat_member(c.message.chat.id, user.id, timedelta(minutes=1))
            logger.info("清理用户：{} {}", c.message.chat.id, user.id)
