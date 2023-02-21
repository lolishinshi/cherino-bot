from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove


from cherino import utils

router = Router()


@router.message(Command("ping"))
async def cmd_ping(message: Message):
    await message.reply("pong", reply_markup=ReplyKeyboardRemove())


@router.message(Command("admin"))
async def cmd_admin(message: Message, bot: Bot):
    admin = "".join(await utils.user.get_admin_mention(message.chat.id, bot))
    await message.reply(
        "{}用户 {} 召唤了管理员".format(admin, message.from_user.mention_html())
    )
    await message.delete()
