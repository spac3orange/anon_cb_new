from aiogram.filters import BaseFilter
from app.core import config_aiogram
from aiogram.types import Message


class IsAdmin(BaseFilter):
    def __init__(self) -> None:
        self.admin_ids = config_aiogram.admin_id

    async def __call__(self, message: Message) -> bool:
        return str(message.from_user.id) in self.admin_ids
