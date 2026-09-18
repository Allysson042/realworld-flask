"""Backwards-compatibility shim (migration step 5).

Step 3 introduced this module as a thin wrapper around
``realworld.api.core.auth``. Step 5 moves the canonical FastAPI dependencies
(``get_current_user`` / ``get_optional_current_user``) into
``realworld.api.core.auth``. This module now re-exports them so any lingering
``from realworld.api.core.fastapi_auth import ...`` imports keep working.
New code must import from ``realworld.api.core.auth`` directly.
"""

from realworld.api.core.auth import (
    get_current_user,
    get_optional_current_user,
    get_optional_user_id,
    get_required_user_id,
)

__all__ = [
    "get_current_user",
    "get_optional_current_user",
    "get_optional_user_id",
    "get_required_user_id",
]
