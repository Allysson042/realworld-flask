import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _database_url() -> str:
    return (
        f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}"
        f":{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
    )


_ENGINE = create_async_engine(_database_url())

_AsyncSession = async_sessionmaker(
    bind=_ENGINE, class_=AsyncSession, expire_on_commit=False
)


@asynccontextmanager
async def get_db_connection():
    """Async context manager for handling database transactions."""
    async with _AsyncSession() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
            await session.rollback()
            raise
