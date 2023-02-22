from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from cherino.filters import IsAdmin, IsGroup
from cherino.scheduler import Scheduler
from cherino.utils.message import add_question_from_message

router = Router()


@router.message(Command("add_question"), IsGroup(), IsAdmin())
async def cmd_add_question(message: Message, scheduler: Scheduler):
    if not message.reply_to_message:
        return

    add_question_from_message(message.reply_to_message)

    reply = await message.reply("添加成功！")
    scheduler.run_after(
        message.reply_to_message.delete(), 5, str(message.reply_to_message.message_id)
    )
    scheduler.run_after(message.delete(), 5, str(message.message_id))
    scheduler.run_after(reply.delete(), 5, str(reply.message_id))
