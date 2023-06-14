from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import ContentType, Message, ReplyKeyboardRemove

from cherino import utils
from cherino.filters import IsGroup
from cherino.scheduler import Scheduler

router = Router()


@router.message(Command("ping"))
async def cmd_ping(message: Message, scheduler: Scheduler):
    chat = message.chat
    reply = await message.reply("pong", reply_markup=ReplyKeyboardRemove())
    scheduler.run_after(message.delete(), 5, f"delete:{chat.id}:{message.message_id}")
    scheduler.run_after(reply.delete(), 5, f"delete:{chat.id}:{reply.message_id}")


@router.message(Command("admin"), IsGroup())
async def cmd_admin(message: Message, bot: Bot):
    admin = "".join(await utils.user.get_admin_mention(message.chat.id, bot))
    await message.reply(
        "{}用户 {} 召唤了管理员".format(admin, message.from_user.mention_html())
    )
    await message.delete()


@router.message(F.content_type == ContentType.LEFT_CHAT_MEMBER)
async def on_user_join(message: Message):
    await message.delete()
