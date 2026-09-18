import os
import typing as typ
from contextlib import asynccontextmanager
from uuid import UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


def _database_url() -> str:
    return (
        f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}"
        f":{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
    )


# NullPool: each checkout opens a fresh connection on the *current* event
# loop. A pooled asyncpg connection is bound to the loop that created it,
# which breaks any test harness mixing loops. Correctness first; pool
# tuning (per-loop pools) is a later optimization.
_ENGINE = create_async_engine(_database_url(), poolclass=NullPool)

_Session = async_sessionmaker(bind=_ENGINE, class_=AsyncSession, expire_on_commit=False)


def coerce_uuid(value: typ.Optional[str]) -> typ.Optional[UUID]:
    """Coerce a UUID-ish bind param for asyncpg.

    asyncpg binds ``str`` params as typed ``varchar``, which PostgreSQL
    refuses to compare against ``uuid`` columns (``uuid = character
    varying``); the previous synchronous driver sent them untyped so the
    coercion used to happen server-side. Convert to ``UUID`` objects up
    front; pass ``None`` through untouched.
    """
    if value is None:
        return None
    return value if isinstance(value, UUID) else UUID(str(value))


@asynccontextmanager
async def get_db_connection() -> typ.AsyncIterator[AsyncSession]:
    """Async context manager for handling database transactions.

    Yields an ``AsyncSession`` backed by the asyncpg driver, so all I/O
    on the request path is genuinely non-blocking. Commits on clean exit,
    rolls back on error.
    """

    async with _Session() as session:
        try:
            yield session
            await session.commit()

        except Exception as e:
            print(f"An error occurred: {e}")
            await session.rollback()
            raise e
