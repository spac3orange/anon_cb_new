from datetime import datetime
from sqlalchemy import update, Select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.future import select
from app.database import User, Dialog
from app.logger import logger

from sqlalchemy.ext.asyncio import AsyncSession


async def add_user(session: AsyncSession, user_id: int, username: str | None = None) -> User | None:
    """
    Асинхронно добавляет нового пользователя в БД или обновляет username, если он изменился.

    Args:
        session: Асинхронная сессия SQLAlchemy
        user_id: Telegram user_id (обязательный)
        username: Telegram username (опционально)

    Returns:
        User: Объект пользователя или None в случае ошибки
    """
    try:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            if user.username != username:
                user.username = username
                await session.commit()
                logger.info(f"Username обновлён для user_id={user_id}: {username}")
            return user

        # Создаем нового пользователя
        new_user = User(
            user_id=user_id,
            username=username
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        logger.info(f"Новый пользователь добавлен: user_id={user_id}, username={username}")

        return new_user

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Ошибка целостности при добавлении пользователя {user_id}: {e}")
        return None

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка SQLAlchemy при работе с пользователем {user_id}: {e}")
        return None

    except Exception as e:
        await session.rollback()
        logger.error(f"Непредвиденная ошибка при работе с пользователем {user_id}: {e}")
        raise


async def set_user_state(session: AsyncSession, user_id: int, state: str):
    """Меняет состояние пользователя"""
    try:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user.user_state = state
            await session.commit()
            await session.refresh(user)
        return user

    except SQLAlchemyError as e:
        logger.error(e)
        return None

    except Exception as e:
        logger.error(e)
        return None


async def find_searching_user(session: AsyncSession, exclude_user_id: int) -> User | None:
    """Ищет другого пользователя, который в поиске"""
    try:
        stmt = select(User).where(User.user_id != exclude_user_id,
                                  User.user_state == "Searching")
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(e)
        return None

    except Exception as e:
        logger.error(e)
        return None


async def create_dialog(session: AsyncSession, user1: User, user2: User) -> Dialog:
    """
    Создаёт диалог между двумя пользователями и обновляет их состояния.
    """
    # генерируем уникальный dialog_id
    dialog_id = int(f"{min(user1.user_id, user2.user_id)}{max(user1.user_id, user2.user_id)}"[:18])

    dialog = Dialog(
        dialog_date=datetime.now(),
        dialog_id=dialog_id,
        user_1_id=user1.user_id,
        user_2_id=user2.user_id
    )
    session.add(dialog)
    await session.commit()
    await session.refresh(dialog)

    # обновляем состояния пользователей
    user1.user_state = "InDialog"
    user2.user_state = "InDialog"
    await session.commit()

    return dialog


async def get_companion_id(session: AsyncSession, user_id: int) -> int | None:
    """
    Возвращает ID собеседника для пользователя, если есть активный диалог.

    Args:
        session: асинхронная сессия SQLAlchemy
        user_id: Telegram user_id пользователя

    Returns:
        int | None: ID собеседника или None, если диалога нет
    """
    try:
        # Ищем активный диалог, где участвует пользователь
        stmt = select(Dialog).where(
            ((Dialog.user_1_id == user_id) | (Dialog.user_2_id == user_id))
        )
        result = await session.execute(stmt)
        dialog = result.scalar_one_or_none()

        if not dialog:
            return None

        # Определяем собеседника
        if dialog.user_1_id == user_id:
            return dialog.user_2_id
        else:
            return dialog.user_1_id

    except Exception as e:
        logger.error(f"Ошибка получения companion_id для user_id={user_id}: {e}")
        return None



async def end_dialog(session: AsyncSession, user_id: int) -> bool:
    """
    Завершает активный диалог пользователя, меняя его статус на 'Closed'.

    Args:
        session: асинхронная сессия SQLAlchemy
        user_id: Telegram user_id пользователя, который хочет завершить диалог

    Returns:
        bool: True, если диалог успешно завершён, False если диалога нет
    """
    try:
        # Находим активный диалог
        stmt = select(Dialog).where(
            ((Dialog.user_1_id == user_id) | (Dialog.user_2_id == user_id)) &
            (Dialog.dialog_status == "Open")
        )
        result = await session.execute(stmt)
        dialog = result.scalar_one_or_none()

        if not dialog:
            return False

        # Меняем статус диалога на 'Closed'
        dialog.dialog_status = "Closed"

        # Возвращаем пользователей в состояние "Offline"
        stmt_users = select(User).where(User.user_id.in_([dialog.user_1_id, dialog.user_2_id]))
        result_users = await session.execute(stmt_users)
        users = result_users.scalars().all()

        for u in users:
            u.user_state = "Offline"

        await session.commit()
        return True

    except Exception as e:
        logger.error(f"Ошибка завершения диалога для user_id={user_id}: {e}")
        await session.rollback()
        return False
