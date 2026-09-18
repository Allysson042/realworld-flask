"""Authentication: JWT handling, password hashing, and FastAPI dependencies.

Migration step 5: this module is the single source of truth for auth logic
exposed as proper FastAPI dependencies (``get_current_user`` /
``get_optional_current_user`` used via ``Depends(...)``), replacing the thin
``fastapi_auth`` wrapper introduced in step 3.

Notes on async behavior (deliberate choices, not oversights):
- JWT encode/decode via PyJWT stays synchronous. It is CPU-light (a single
  HMAC + base64 round-trip) and needs no special async handling.
- bcrypt (password hashing/verification) is CPU-bound with no native asyncio
  API. Calling it directly inside ``async def`` code would block the event
  loop for the duration of the hash/verify call, so every bcrypt call site
  below is wrapped with ``fastapi.concurrency.run_in_threadpool`` to run it
  off the event loop. The hashing algorithm and parameters are unchanged;
  only how the call is invoked changed.
"""

import os

import bcrypt
import jwt
import typing as typ
from functools import lru_cache, wraps
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException
from fastapi.concurrency import run_in_threadpool

try:
    from flask import request as _flask_request
except Exception:  # Flask not installed (pure ASGI context)
    _flask_request = None  # type: ignore[assignment]

ISSUER = "realworld"
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
OVERRIDE_TOKEN_EXPIRATION = os.getenv("OVERRIDE_TOKEN_EXPIRATION", "FALSE").upper()


#
# JWT (CPU-light: stays synchronous, no threadpool needed)
#
def generate_jwt(
    user_id: str,
):
    payload = {
        "iss": ISSUER,
        "user_id": user_id,
        "iat": datetime.now(tz=timezone.utc),
    }
    if OVERRIDE_TOKEN_EXPIRATION == "TRUE":
        payload["exp"] = datetime.now(tz=timezone.utc) + timedelta(minutes=15)

    # CPU-light HMAC signing; safe to call directly from async code.
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@lru_cache()
def _decode_jwt(token: str) -> typ.Tuple[bool, typ.Union[dict, str]]:
    try:
        # CPU-light HMAC verification; safe to call directly from async code.
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True, decoded
    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        jwt.InvalidSignatureError,
    ) as e:
        return False, str(e)
    except Exception:
        return False, "Unknown token error."


#
# Password hashing (CPU-bound: must run off the event loop)
#
def hash_password_sync(password: str) -> str:
    """Synchronous bcrypt hash (same algorithm/parameters as before).

    Kept for synchronous callers (tests, seeding scripts). Async request
    code must use :func:`hash_password` below instead.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


async def hash_password(password: str) -> str:
    """Hash a password without blocking the event loop."""
    # bcrypt is CPU-bound with no asyncio API; run it in a threadpool so the
    # event loop stays responsive while hashing. Algorithm/params unchanged.
    return await run_in_threadpool(hash_password_sync, password)


def verify_password_sync(password: str, hashed_password: str) -> bool:
    """Synchronous bcrypt verification (same algorithm/parameters as before)."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


async def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password without blocking the event loop."""
    # bcrypt is CPU-bound with no asyncio API; run it in a threadpool so the
    # event loop stays responsive while verifying. Algorithm/params unchanged.
    return await run_in_threadpool(verify_password_sync, password, hashed_password)


async def is_valid_password(password: str, hashed_password: str) -> bool:
    """Async alias kept for handler compatibility; see :func:`verify_password`."""
    # bcrypt is CPU-bound with no asyncio API; delegate to the threadpooled
    # verifier so async callers never block the event loop on this call.
    return await verify_password(password, hashed_password)


#
# Legacy Flask helpers (kept so the Flask blueprints keep working during
# the migration; new FastAPI code must use the dependencies below).
#
def _get_token_from_request() -> typ.Optional[str]:
    if _flask_request is None:
        return None
    encoded_token = _flask_request.headers.get("Authorization")
    if not encoded_token:
        return None

    # Authorization: Token <token>
    return encoded_token.split(" ")[1]


def validate_token(func):
    @wraps(func)
    def wrapper(*args, **kwds):

        encoded_token = _get_token_from_request()
        if not encoded_token:
            return {"error": "No token provided."}, 401

        is_valid, decoded = _decode_jwt(encoded_token)
        if not is_valid:
            return {"error": decoded}, 401

        return func(*args, **kwds)

    return wrapper


def get_user_id_from_token() -> typ.Optional[str]:
    is_valid, decoded = _decode_jwt(_get_token_from_request())
    if is_valid:
        return decoded.get("user_id")
    return None


#
# FastAPI dependencies
#
def _extract_token(
    authorization: typ.Optional[str] = None,
) -> typ.Optional[str]:
    if not authorization:
        return None
    # Authorization: Token <token>
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or not parts[1]:
        return None
    return parts[1]


def get_optional_current_user(
    authorization: typ.Optional[str] = Header(default=None),
) -> typ.Optional[str]:
    """Optional auth dependency: user_id from a valid token, else None.

    Never raises; for public endpoints that personalize when a token is
    present (list/get articles, list comments, get profile).
    """
    token = _extract_token(authorization)
    if not token:
        return None
    is_valid, decoded = _decode_jwt(token)
    if not is_valid:
        return None
    return decoded.get("user_id")


def get_current_user(
    authorization: typ.Optional[str] = Header(default=None),
) -> str:
    """Required auth dependency: user_id from a valid token, else 401.

    Use via ``Depends(get_current_user)`` on every route the RealWorld spec
    marks as requiring authentication.
    """
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="No token provided.")

    is_valid, decoded = _decode_jwt(token)
    if not is_valid:
        raise HTTPException(status_code=401, detail=decoded)

    return decoded.get("user_id")


# Backwards-compatible aliases for the step-3 wrapper names, so existing
# ``Depends(get_required_user_id)`` / ``Depends(get_optional_user_id)``
# wiring keeps working while routers migrate to the canonical names above.
def get_optional_user_id(
    authorization: typ.Optional[str] = Header(default=None),
) -> typ.Optional[str]:
    return get_optional_current_user(authorization)


def get_required_user_id(
    authorization: typ.Optional[str] = Header(default=None),
) -> str:
    return get_current_user(authorization)
