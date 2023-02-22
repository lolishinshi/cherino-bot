from aiogram.types import Message

from cherino import crud


def add_question_from_message(message: Message):
    if message.photo:
        image, text = message.photo[-1].file_id, message.caption
    else:
        image, text = None, message.text

    question, *answers = text.splitlines()
    crud.auth.add_question(message.chat.id, question, answers, image)
