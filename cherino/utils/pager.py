import abc

from aiogram.handlers import CallbackQueryHandler
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class PagerCallback(CallbackData, prefix="pager"):
    name: str
    page: int


class AbstractPager(CallbackQueryHandler, metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def text(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def get_page(self, page: int = 0) -> InlineKeyboardBuilder:
        pass

    async def handle(self):
        if not isinstance(self.data["callback_data"], PagerCallback):
            page = 0
        else:
            callback_data: PagerCallback = self.data["callback_data"]
            page = callback_data.page

        builder = self.get_page(page)
        builder.button(
            text="<", callback_data=PagerCallback(name=self.name, page=max(page - 1, 0))
        )
        builder.button(
            text=">", callback_data=PagerCallback(name=self.name, page=page + 1)
        )
        builder.adjust(*([1] * (len(list(builder.buttons)) - 2)), 2)

        await self.message.edit_text(text=self.text, reply_markup=builder.as_markup())
