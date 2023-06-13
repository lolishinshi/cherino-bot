from aiogram.types import Chat

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
