from aiogram import Bot
from aiogram.types import Message
from loguru import logger
from cherino import crud
from cherino.recent_message import RecentMessage


def add_question_from_message(message: Message):
    if message.photo:
        image, text = message.photo[-1].file_id, message.caption
    else:
        image, text = None, message.text

    question, *answers = text.splitlines()
    crud.auth.add_question(message.chat.id, question, answers, image)


async def delete_all_message(
    bot: Bot, chat_id: int, user_id: int, recent_message: RecentMessage
):
    """
    删除用户所有消息
    """
    messages = recent_message.get(chat_id, user_id)
    for msg_id in messages:
        try:
            logger.debug("删除消息 {} {}", chat_id, msg_id)
            await bot.delete_message(chat_id, msg_id)
        except:
            pass
