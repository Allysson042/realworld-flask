import typing as typ
from logging import Logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text as satext
from sqlalchemy.exc import IntegrityError

from realworld.api.core import auth as auth_module
from realworld.api.core.db import coerce_uuid
from realworld.api.core.models import DBUser
from .models import UpdateUserData, RegisterUserData, UserData


logger = Logger(__name__)


def hash_password(password: str) -> str:
    # Sync wrapper kept for synchronous callers (tests/seeds). Same
    # bcrypt algorithm/parameters; async request code awaits
    # ``auth_module.hash_password`` (threadpooled) instead.
    return auth_module.hash_password_sync(password)


def is_valid_password(password: str, hashed_password: str) -> bool:
    # Sync wrapper kept for synchronous callers. Same bcrypt check;
    # async request code awaits ``auth_module.verify_password``
    # (threadpooled) instead.
    return auth_module.verify_password_sync(password, hashed_password)


async def create_user(
    db_session: AsyncSession, data: RegisterUserData
) -> typ.Optional[DBUser]:
    try:
        # bcrypt is CPU-bound with no asyncio API; hash off the event loop
        # via the threadpooled auth helper (algorithm/params unchanged).
        password_hash = await auth_module.hash_password(data.password)
        result = (
            await db_session.execute(
                satext(
                    """
                    INSERT INTO users (username, email, password_hash)
                    VALUES (:username, :email, :password_hash)
                    ON CONFLICT (username) DO NOTHING
                    RETURNING id, username, email, bio, image_url, created_date, updated_date
                    """
                ).bindparams(
                    username=data.username,
                    email=data.email,
                    password_hash=password_hash,
                )
            )
        ).fetchone()

    except IntegrityError:
        await db_session.rollback()
        return None

    if result:
        return DBUser(
            user_id=str(result.id),
            username=result.username,
            email=result.email,
            bio=result.bio,
            image=result.image_url,
        )
    return None


async def update_user(
    db_session: AsyncSession, user_id: str, data: UpdateUserData
) -> typ.Optional[UserData]:
    result = (
        await db_session.execute(
            satext(
                """
                UPDATE users
                SET email = :email,
                    bio = :bio,
                    image_url = :image,
                    updated_date = CURRENT_TIMESTAMP
                WHERE id = :user_id
                RETURNING username, email, bio, image_url
                """
            ).bindparams(
                user_id=coerce_uuid(user_id),
                email=data.email,
                bio=data.bio,
                image=data.image,
            )
        )
    ).fetchone()

    if result:
        return UserData(
            username=result.username,
            email=result.email,
            bio=result.bio,
            image=result.image_url,
        )
    return None


async def validate_user_creds(
    db_session: AsyncSession, email: str, password: str
) -> typ.Optional[DBUser]:
    result = (
        await db_session.execute(
            satext(
                """
                SELECT id, username, email, password_hash, bio, image_url
                FROM users
                WHERE email = :email
                """
            ).bindparams(email=email)
        )
    ).fetchone()

    if not result:
        return None

    # bcrypt is CPU-bound with no asyncio API; verify off the event loop
    # via the threadpooled auth helper (algorithm/params unchanged).
    if await auth_module.verify_password(password, result.password_hash):
        return DBUser(
            user_id=str(result.id),
            username=result.username,
            email=result.email,
            bio=result.bio,
            image=result.image_url,
        )

    return None


async def get_user(db_session: AsyncSession, user_id: str) -> typ.Optional[UserData]:
    result = (
        await db_session.execute(
            satext(
                """
                SELECT id, username, email, bio, image_url, created_date, updated_date
                FROM users
                WHERE id = :user_id
                """
            ).bindparams(user_id=coerce_uuid(user_id))
        )
    ).fetchone()

    if result:
        return UserData(
            username=result.username,
            email=result.email,
            bio=result.bio,
            image=result.image_url,
        )
    return None
