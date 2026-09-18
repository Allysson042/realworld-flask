from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("")
def get_tags():
    raise HTTPException(status_code=501)
