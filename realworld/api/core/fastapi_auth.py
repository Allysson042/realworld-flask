"""Thin FastAPI auth dependencies wrapping the existing Flask auth logic.

Intermediate migration state (step 3): this module does NOT rewrite
``realworld.api.core.auth``. It reuses ``_decode_jwt`` as-is and only adapts
the transport (FastAPI ``Authorization`` header instead of the Flask
``request`` object). The wrapped calls are synchronous/blocking; proper
async auth is revisited in the later auth step.
"""

import typing as typ

from fastapi import Header, HTTPException

from realworld.api.core.auth import _decode_jwt


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


def get_optional_user_id(
    authorization: typ.Optional[str] = Header(default=None),
) -> typ.Optional[str]:
    """Return the user_id from the token, or None if missing/invalid.

    Mirrors Flask's ``get_user_id_from_token()`` usage on endpoints that do
    not require authentication (never raises).
    """
    token = _extract_token(authorization)
    if not token:
        return None
    is_valid, decoded = _decode_jwt(token)
    if not is_valid:
        return None
    return decoded.get("user_id")


def get_required_user_id(
    authorization: typ.Optional[str] = Header(default=None),
) -> str:
    """Return the user_id, raising 401 if the token is missing/invalid.

    Mirrors Flask's ``validate_token`` decorator behavior as-is.
    """
    token = _extract_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="No token provided.")

    is_valid, decoded = _decode_jwt(token)
    if not is_valid:
        raise HTTPException(status_code=401, detail=decoded)

    return decoded.get("user_id")
