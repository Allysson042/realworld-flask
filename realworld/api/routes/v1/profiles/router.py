from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/{username}")
def get_profile(username: str):
    raise HTTPException(status_code=501)


@router.post("/{username}/follow")
def follow_profile(username: str):
    raise HTTPException(status_code=501)


@router.delete("/{username}/follow")
def unfollow_profile(username: str):
    raise HTTPException(status_code=501)
