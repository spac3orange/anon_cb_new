import asyncio

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.core import aiogram_bot
from app.logger import logger
from app.handlers import (start)
from app.keyboards import set_commands_menu
from app.database import initialize_database, engine

async def start_params() -> None:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    logger.info('Bot started')

    # # инициализация БД
    await initialize_database(engine)


    await set_commands_menu(aiogram_bot)
    # Пропускаем накопившиеся апдейты и запускаем polling
    await aiogram_bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(aiogram_bot)


async def main():
    task1 = asyncio.create_task(start_params())
    await asyncio.gather(task1)


if __name__ == '__main__':
    asyncio.run(main())
