from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import ContentType, Message, ReplyKeyboardRemove

from cherino import utils

router = Router()


@router.message(Command("ping"))
async def cmd_ping(message: Message):
    print(message.json())
    await message.reply("pong", reply_markup=ReplyKeyboardRemove())


@router.message(Command("admin"))
async def cmd_admin(message: Message, bot: Bot):
    admin = "".join(await utils.user.get_admin_mention(message.chat.id, bot))
    await message.reply(
        "{}用户 {} 召唤了管理员".format(admin, message.from_user.mention_html())
    )
    await message.delete()


@router.message(F.content_type == ContentType.LEFT_CHAT_MEMBER)
async def on_user_join(message: Message):
    await message.delete()
