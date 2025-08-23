import asyncio
import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

API_TOKEN = "7654937584:AAEk3cVYxVRptToTtPMp62QVGkWYr97reTg"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Подключение к Redis
redis_conn = redis.from_url("redis://localhost", decode_responses=True)

QUEUE_KEY = "chat:queue"      # очередь пользователей
PAIR_KEY_PREFIX = "chat:pair:"  # пары пользователей
PAIR_TTL = 600   # время жизни пары (секунд) = 10 минут
QUEUE_TTL = 300  # время жизни очереди = 5 минут


async def add_to_queue(user_id: int):
    """Добавляем пользователя в очередь с TTL"""
    await redis_conn.rpush(QUEUE_KEY, user_id)
    # ставим время жизни очереди
    await redis_conn.expire(QUEUE_KEY, QUEUE_TTL)


async def get_from_queue() -> int | None:
    """Берём первого пользователя из очереди"""
    return await redis_conn.lpop(QUEUE_KEY)


async def set_pair(user1: int, user2: int):
    """Запоминаем пару с TTL"""
    await redis_conn.set(f"{PAIR_KEY_PREFIX}{user1}", user2, ex=PAIR_TTL)
    await redis_conn.set(f"{PAIR_KEY_PREFIX}{user2}", user1, ex=PAIR_TTL)


async def get_pair(user_id: int) -> int | None:
    """Получаем собеседника"""
    return await redis_conn.get(f"{PAIR_KEY_PREFIX}{user_id}")


async def remove_pair(user_id: int):
    """Удаляем пару при выходе"""
    partner = await get_pair(user_id)
    if partner:
        await redis_conn.delete(f"{PAIR_KEY_PREFIX}{partner}")
    await redis_conn.delete(f"{PAIR_KEY_PREFIX}{user_id}")


# ======================= ХЕНДЛЕРЫ =======================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Нажми /search чтобы найти собеседника.")


@dp.message(Command("search"))
async def cmd_search(message: Message):
    user_id = message.from_user.id
    other_user = await get_from_queue()

    if other_user:
        # Соединяем
        await set_pair(user_id, int(other_user))
        await message.answer("✅ Собеседник найден! Пишите сообщение.")
        await bot.send_message(int(other_user), "✅ Собеседник найден! Пишите сообщение.")
    else:
        # Кладём в очередь
        await add_to_queue(user_id)
        await message.answer("⏳ Ожидание собеседника...")


@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    await remove_pair(message.from_user.id)
    await message.answer("❌ Вы вышли из чата.")


@dp.message()
async def chat_handler(message: Message):
    """Пересылаем сообщения собеседнику"""
    partner = await get_pair(message.from_user.id)
    if partner:
        await bot.send_message(int(partner), message.text)
    else:
        await message.answer("⚠️ У вас сейчас нет собеседника. Введите /search")


# ======================= MAIN =======================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
