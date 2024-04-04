from datetime import datetime, timedelta
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message
from cherino import crud


class RecentMessageMiddleware(BaseMiddleware):
    """
    记录一个小时之内，每个用户发送的消息 ID
    """

    def __init__(self):
        self.recent_message = RecentMessage()

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ):
        if not event.from_user.is_bot and isinstance(event, Message):
            self.recent_message.add(event.chat.id, event.from_user.id, event.message_id)
            crud.user.update_user_last_seen(event.from_user.id, event.chat.id)
        data["recent_message"] = self.recent_message
        return await handler(event, data)


class RecentMessage:
    """
    记录一个小时之内，每个用户发送的消息 ID
    """

    def __init__(self):
        self.message: dict[int, dict[int, list[tuple[int, datetime]]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def add(self, chat_id: int, user_id: int, message_id: int):
        """
        增加一条消息记录，并删除超过一个小时的记录
        """
        message_list = self.message[chat_id][user_id]
        message_list.append((message_id, datetime.now()))
        while datetime.now() - message_list[0][1] > timedelta(hours=1):
            message_list.pop(0)

    def get(self, chat_id: int, user_id: int) -> list[int]:
        """
        获取一个用户在一个小时内发送的消息 ID
        """
        messages = [x[0] for x in self.message[chat_id][user_id]]
        self.message[chat_id][user_id].clear()
        return messages
