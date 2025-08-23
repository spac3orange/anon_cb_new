# from databases import Database
from environs import Env
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

env = Env()
env.read_env()

# Стартовая база
DATABASE_URL = env('DB_PATH')

# database = Database(DATABASE_URL)
Base = declarative_base()

engine = create_async_engine(DATABASE_URL, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

