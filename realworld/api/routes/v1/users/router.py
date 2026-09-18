from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/users")
def create_user():
    raise HTTPException(status_code=501)


@router.post("/users/login")
def authenticate_user():
    raise HTTPException(status_code=501)


@router.get("/user")
def get_current_user():
    raise HTTPException(status_code=501)


@router.put("/user")
def update_user():
    raise HTTPException(status_code=501)
