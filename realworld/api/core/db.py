import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_ENGINE = create_async_engine(
    f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}",
    pool_pre_ping=True,
)

_AsyncSession = async_sessionmaker(
    bind=_ENGINE, class_=AsyncSession, expire_on_commit=False
)


@asynccontextmanager
async def get_db_connection():
    """Async context manager for handling database transactions.

    Yields an :class:`AsyncSession` backed by the asyncpg driver and
    commits on clean exit / rolls back on error (mirrors the old sync
    helper's semantics, but genuinely non-blocking).
    """

    async with _AsyncSession() as session:
        try:
            yield session
            await session.commit()

        except Exception as e:
            print(f"An error occurred: {e}")
            await session.rollback()
            raise e
