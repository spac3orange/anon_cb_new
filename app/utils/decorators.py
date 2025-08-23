from functools import wraps
from app.database.db_session import AsyncSessionLocal  # укажи верный путь

def with_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with AsyncSessionLocal() as session:
            return await func(*args, session=session, **kwargs)
    return wrapper
