import asyncio
import os
import redis.asyncio as redis
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from app2.logger import logger
from environs import Env
from app2.keyboards import set_commands_menu

env = Env()
env.read_env()
API_TOKEN = env('TOKEN')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Подключение к Redis
redis_conn = redis.from_url("redis://localhost", decode_responses=True)

QUEUE_KEY = "chat:queue"      # очередь пользователей
PAIR_KEY_PREFIX = "chat:pair:"  # пары пользователей
QUEUE_TTL = 300  # время жизни очереди = 5 минут

# Папки для медиа
MEDIA_DIR = "media"
MEDIA_FOLDERS = {
    "photo": "photos",
    "video": "videos",
    "document": "docs",
    "voice": "voice",
    "audio": "audio"
}
for folder in MEDIA_FOLDERS.values():
    os.makedirs(os.path.join(MEDIA_DIR, folder), exist_ok=True)


async def add_to_queue(user_id: int):
    """Добавляем пользователя в очередь с TTL"""
    await redis_conn.rpush(QUEUE_KEY, user_id)
    await redis_conn.expire(QUEUE_KEY, QUEUE_TTL)


async def get_from_queue() -> int | None:
    """Берём первого пользователя из очереди"""
    return await redis_conn.lpop(QUEUE_KEY)


async def set_pair(user1: int, user2: int):
    """Запоминаем пару (без TTL)"""
    await redis_conn.set(f"{PAIR_KEY_PREFIX}{user1}", user2)
    await redis_conn.set(f"{PAIR_KEY_PREFIX}{user2}", user1)


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
    logger.info(f"User {message.from_user.id} used /start")
    inf_me = (
        f'{message.from_user.id}=@{message.from_user.username} подключился'
    )
    await bot.send_message(chat_id=462813109, text=inf_me)
    await message.answer("Привет!"
                         "\nПросто нажми /search, чтобы найти собеседника"
                         "\n\nПриятного общения!⭐️")


@dp.message(Command("search"))
async def cmd_search(message: Message):
    user_id = message.from_user.id
    logger.info(f"User {user_id} used /search")

    # Проверяем, есть ли текущий собеседник
    partner = await get_pair(user_id)
    if partner:
        # Уведомляем обоих, что чат завершён
        await bot.send_message(partner, "❌ Ваш собеседник завершил диалог."
                                        "\n /search для поиска нового собеседника")
        await message.answer("❌ Диалог завершён."
                             "\n ⏳ Поиск нового собеседника...")
        await remove_pair(user_id)
        logger.info(f"Chat closed: {user_id} <-> {partner}")

    # Берём следующего из очереди
    other_user = await get_from_queue()

    if other_user:
        await set_pair(user_id, int(other_user))
        await message.answer("✅ Собеседник найден! Можете начать общение.")
        await bot.send_message(int(other_user), "✅ Собеседник найден! Можете начать общение.")
        logger.info(f"Pair created: {user_id} <-> {other_user}")
    else:
        await add_to_queue(user_id)
        await message.answer("⏳ Ожидание собеседника...")
        logger.info(f"User {user_id} added to queue")


@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    user_id = message.from_user.id
    await remove_pair(user_id)
    await message.answer("❌ Вы вышли из чата."
                         "\nЖми /search для поиска нового собеседника")
    logger.info(f"User {user_id} left chat")


# ========== ХЕНДЛЕР ДЛЯ ПЕРЕСЫЛКИ ЛЮБЫХ СООБЩЕНИЙ ==========
@dp.message(F.content_type.in_({"text", "photo", "video", "voice", "document", "audio", "sticker"}))
async def chat_handler(message: Message):
    user_id = message.from_user.id
    partner = await get_pair(user_id)

    if not partner:
        await message.answer("⚠️ У вас сейчас нет собеседника. Введите /search")
        logger.info(f"User {user_id} tried to send message without partner")
        return

    # Логируем
    if message.text:
        logger.info(f"User {user_id} -> {partner}: {message.text}")
    else:
        logger.info(f"User {user_id} -> {partner}: sent {message.content_type}")

    # Сохраняем медиа по папкам
    if message.content_type in ["photo", "video", "voice", "document", "audio"]:
        if message.photo:  # фото — берём самое качественное
            file_id = message.photo[-1].file_id
            folder = MEDIA_FOLDERS["photo"]
        elif message.video:
            file_id = message.video.file_id
            folder = MEDIA_FOLDERS["video"]
        elif message.voice:
            file_id = message.voice.file_id
            folder = MEDIA_FOLDERS["voice"]
        elif message.audio:
            file_id = message.audio.file_id
            folder = MEDIA_FOLDERS["audio"]
        else:  # документ
            file_id = message.document.file_id
            folder = MEDIA_FOLDERS["document"]

        file = await bot.get_file(file_id)
        file_path = file.file_path
        filename = f"{user_id}_{message.message_id}_{os.path.basename(file_path)}"

        save_path = os.path.join(MEDIA_DIR, folder, filename)
        await bot.download_file(file_path, save_path)
        logger.info(f"Media saved: {save_path}")

    # Пересылаем собеседнику
    await bot.copy_message(chat_id=int(partner), from_chat_id=message.chat.id, message_id=message.message_id)


# ======================= MAIN =======================

async def main():
    await set_commands_menu(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
