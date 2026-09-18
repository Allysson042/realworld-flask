from fastapi import APIRouter

from realworld.api.core.db import get_db_connection
from realworld.api.routes.v1.articles import handler as articles_handler
from realworld.api.routes.v1.articles.models import GetTagsResponse

router = APIRouter()


@router.get("", response_model=GetTagsResponse)
async def get_tags():
    async with get_db_connection() as db_session:
        tags = await articles_handler.get_all_tags(db_session)

    return GetTagsResponse(tags=tags)
