from io import BytesIO

import aiohttp
from aiogram import Bot
from aiogram.types import Message

from cherino.config import CONFIG


async def download_image(bot: Bot, message: Message) -> bytes:
    if message.photo:
        photo = message.photo[-1]
        photo = await bot.download(photo.file_id)
        return photo.read()
    elif message.video:
        photo = await bot.download(message.video.thumbnail.file_id)
        return photo.read()
    elif message.document:
        photo = await bot.download(message.document.thumbnail.file_id)
        return photo.read()
    elif message.animation:
        photo = await bot.download(message.animation.thumbnail.file_id)
        return photo.read()
    # sticker ?


async def detect_nsfw(image: bytes) -> dict[str, float]:
    """
    使用 nsfw model 检测图片，返回一个字典，key 为类别，value 为置信度（0~1）
    key 的可能值有：drawings, hentai, neutral, porn, sexy
    :param image:
    :return:
    """
    url = CONFIG.nsfw_api
    data = aiohttp.FormData()
    data.add_field("images", BytesIO(image))
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            resp = await resp.json()
            return resp[0]
