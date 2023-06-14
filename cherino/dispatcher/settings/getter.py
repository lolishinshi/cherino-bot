from aiogram.types import Chat
from loguru import logger

from cherino.crud import auth
from cherino.crud.setting import Settings, get_setting


async def setting_getter(event_chat: Chat, **kwargs) -> dict:
    return {Settings.BAN_TIME: get_setting(event_chat.id, Settings.BAN_TIME)}


async def question_getter(event_chat: Chat, **kwargs) -> dict:
    return {"questions": auth.get_all_questions(event_chat.id)}


async def answer_stats_getter(event_chat: Chat, **kwargs) -> dict:
    questions = auth.get_answer_stats(event_chat.id)
    texts = []
    for q, total, correct in questions:
        texts.append(
            f"{correct / total * 100:.1f}% - {correct}/{total} - {q.description} - {q.correct_answer.description}"
        )
    text = "\n".join(texts)
    return {"answer_stats": text}


async def purge_list_getter(event_chat: Chat, **kwargs) -> dict:
    from cherino.pyrogram import get_chat_members

    users = []
    async for user in get_chat_members(event_chat.id):
        _, correct = auth.get_user_answer_stats(event_chat.id, user.id)
        if correct == 0:
            users.append(
                f"{user.id} - @{user.username} - {user.first_name} {user.last_name}"
            )
    users = "\n".join(users)
    return {"purge_list": users}
