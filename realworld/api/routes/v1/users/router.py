from fastapi import APIRouter, Depends, HTTPException

from realworld.api.core.auth import generate_jwt
from realworld.api.core.db import get_db_connection
from realworld.api.core.fastapi_auth import get_required_user_id
from realworld.api.routes.v1.users import handler as users_handler
from realworld.api.routes.v1.users.models import (
    AuthUser,
    AuthUserResponse,
    LoginUserRequest,
    RegisterUserRequest,
    UpdateUserRequest,
)

router = APIRouter()


@router.post("/users", response_model=AuthUserResponse)
async def create_user(payload: RegisterUserRequest):
    async with get_db_connection() as db_session:
        user = await users_handler.create_user(db_session, payload.user)
        if not user:
            raise HTTPException(
                status_code=409,
                detail="A user with this username already exists.",
            )

    return AuthUserResponse(
        user=AuthUser(
            email=user.email,
            token=generate_jwt(user.user_id),
            username=user.username,
            bio=user.bio,
            image=user.image,
        )
    )


@router.post("/users/login", response_model=AuthUserResponse)
async def authenticate_user(payload: LoginUserRequest):
    async with get_db_connection() as db_session:
        user = await users_handler.validate_user_creds(
            db_session, email=payload.user.email, password=payload.user.password
        )
        if not user:
            raise HTTPException(status_code=404, detail="User does not exist.")

    return AuthUserResponse(
        user=AuthUser(
            email=user.email,
            token=generate_jwt(user.user_id),
            username=user.username,
            bio=user.bio,
            image=user.image,
        )
    )


@router.get("/user", response_model=AuthUserResponse)
async def get_current_user(user_id: str = Depends(get_required_user_id)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token.")

    async with get_db_connection() as db_session:
        user = await users_handler.get_user(db_session, user_id)
        if user:
            return AuthUserResponse(
                user=AuthUser(
                    email=user.email,
                    token=generate_jwt(user_id),
                    username=user.username,
                    bio=user.bio,
                    image=user.image,
                )
            )

    raise HTTPException(status_code=404, detail="User does not exist.")


@router.put("/user", response_model=AuthUserResponse)
async def update_user(
    payload: UpdateUserRequest,
    user_id: str = Depends(get_required_user_id),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token.")

    async with get_db_connection() as db_session:
        user = await users_handler.update_user(db_session, user_id, payload.user)
        if not user:
            raise HTTPException(status_code=404, detail="User does not exist.")

    return AuthUserResponse(
        user=AuthUser(
            email=user.email,
            token=generate_jwt(user_id),
            username=user.username,
            bio=user.bio,
            image=user.image,
        )
    )
