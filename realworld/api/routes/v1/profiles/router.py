import typing as typ

from fastapi import APIRouter, Depends, HTTPException

from realworld.api.core.auth import (
    get_current_user,
    get_optional_current_user,
)
from realworld.api.core.db import get_db_connection
from realworld.api.routes.v1.profiles import handler as profiles_handler
from realworld.api.routes.v1.profiles.models import (
    ProfileData,
    ProfileDataResponse,
)

router = APIRouter()


@router.get("/{username}", response_model=ProfileDataResponse)
async def get_profile(
    username: str,
    curr_user_id: typ.Optional[str] = Depends(get_optional_current_user),
):
    async with get_db_connection() as db_session:
        profile = await profiles_handler.get_profile(db_session, username, curr_user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")

    return ProfileDataResponse(
        profile=ProfileData(
            username=profile.username,
            bio=profile.bio,
            image=profile.image,
            following=profile.following,
        )
    )


@router.post("/{username}/follow", response_model=ProfileDataResponse)
async def follow_profile(
    username: str,
    curr_user_id: str = Depends(get_current_user),
):
    async with get_db_connection() as db_session:
        profile = await profiles_handler.follow_profile(
            db_session, username, curr_user_id
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")

    return ProfileDataResponse(
        profile=ProfileData(
            username=profile.username,
            bio=profile.bio,
            image=profile.image,
            following=profile.following,
        )
    )


@router.delete("/{username}/follow", response_model=ProfileDataResponse)
async def unfollow_profile(
    username: str,
    curr_user_id: str = Depends(get_current_user),
):
    async with get_db_connection() as db_session:
        profile = await profiles_handler.unfollow_profile(
            db_session, username, curr_user_id
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")

    return ProfileDataResponse(
        profile=ProfileData(
            username=profile.username,
            bio=profile.bio,
            image=profile.image,
            following=profile.following,
        )
    )
