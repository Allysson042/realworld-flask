from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/articles")
def get_articles():
    raise HTTPException(status_code=501)


@router.get("/articles/feed")
def get_feed():
    raise HTTPException(status_code=501)


@router.get("/articles/{slug}")
def get_article(slug: str):
    raise HTTPException(status_code=501)


@router.post("/articles")
def create_article():
    raise HTTPException(status_code=501)


@router.put("/articles/{slug}")
def update_article(slug: str):
    raise HTTPException(status_code=501)


@router.delete("/articles/{slug}")
def delete_article(slug: str):
    raise HTTPException(status_code=501)


@router.post("/articles/{slug}/comments")
def create_comment(slug: str):
    raise HTTPException(status_code=501)


@router.get("/articles/{slug}/comments")
def get_comments(slug: str):
    raise HTTPException(status_code=501)


@router.delete("/articles/{slug}/comments/{comment_id}")
def delete_comment(slug: str, comment_id: str):
    raise HTTPException(status_code=501)


@router.post("/articles/{slug}/favorite")
def favorite_article(slug: str):
    raise HTTPException(status_code=501)


@router.delete("/articles/{slug}/favorite")
def unfavorite_article(slug: str):
    raise HTTPException(status_code=501)
