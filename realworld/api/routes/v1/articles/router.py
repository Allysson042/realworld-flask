import typing as typ

from fastapi import APIRouter, Depends, HTTPException

from realworld.api.core.auth import (
    get_current_user,
    get_optional_current_user,
)
from realworld.api.core.db import get_db_connection
from realworld.api.routes.v1.articles import handler as articles_handler
from realworld.api.routes.v1.articles.models import (
    CreateArticleRequest,
    CreateCommentRequest,
    CreateCommentResponse,
    MultipleArticlesResponse,
    MultipleCommentsResponse,
    SingleArticleResponse,
    UpdateArticleRequest,
)

router = APIRouter()


@router.get("/articles", response_model=MultipleArticlesResponse)
async def get_articles(
    tag: typ.Optional[str] = None,
    author: typ.Optional[str] = None,
    favorited: typ.Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    curr_user_id: typ.Optional[str] = Depends(get_optional_current_user),
):
    """Returns most recent articles globally by default, provide tag, author
    or favorited query parameter to filter results."""
    async with get_db_connection() as db_session:
        articles = await articles_handler.get_articles(
            db_session,
            curr_user_id=curr_user_id,
            filter_tag=tag,
            author_username_filter=author,
            favorited_by_username_filter=favorited,
            limit=limit,
            offset=offset,
        )

    return MultipleArticlesResponse(
        articles=articles,
        articles_count=len(articles),
    )


@router.get("/articles/feed", response_model=MultipleArticlesResponse)
async def get_feed(
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user),
):
    """Returns articles created by followed users, ordered by most recent
    first."""
    async with get_db_connection() as db_session:
        articles = await articles_handler.get_feed_articles(
            db_session,
            user_id,
            limit=limit,
            offset=offset,
        )

    return MultipleArticlesResponse(
        articles=articles,
        articles_count=len(articles),
    )


@router.get("/articles/{slug}", response_model=SingleArticleResponse)
async def get_article(
    slug: str,
    curr_user_id: typ.Optional[str] = Depends(get_optional_current_user),
):
    async with get_db_connection() as db_session:
        article = await articles_handler.get_article_by_slug(
            db_session, slug, curr_user_id=curr_user_id
        )
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

    return SingleArticleResponse(article=article)


@router.post("/articles", response_model=SingleArticleResponse)
async def create_article(
    payload: CreateArticleRequest,
    user_id: str = Depends(get_current_user),
):
    async with get_db_connection() as db_session:
        article = await articles_handler.create_article(
            db_session, user_id, payload.article
        )

    return SingleArticleResponse(article=article)


@router.put("/articles/{slug}", response_model=SingleArticleResponse)
async def update_article(
    slug: str,
    payload: UpdateArticleRequest,
    user_id: str = Depends(get_current_user),
):
    async with get_db_connection() as db_session:
        article = await articles_handler.update_article(
            db_session, slug, user_id, payload.article
        )
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

    return SingleArticleResponse(article=article)


@router.delete("/articles/{slug}")
async def delete_article(
    slug: str,
    user_id: str = Depends(get_current_user),
):
    async with get_db_connection() as db_session:
        if not await articles_handler.delete_article(db_session, slug, user_id):
            raise HTTPException(status_code=404, detail="Article not found")

    return {"message": "Article deleted"}


#
# Comments
#
@router.post("/articles/{slug}/comments", response_model=CreateCommentResponse)
async def create_comment(
    slug: str,
    payload: CreateCommentRequest,
    user_id: str = Depends(get_current_user),
):
    async with get_db_connection() as db_session:
        does_article_exist, comment = await articles_handler.create_article_comment(
            db_session, slug, user_id, payload.comment
        )
        if not does_article_exist:
            raise HTTPException(status_code=404, detail="Article not found")

    return CreateCommentResponse(comment=comment)


@router.get("/articles/{slug}/comments", response_model=MultipleCommentsResponse)
async def get_comments(
    slug: str,
    curr_user_id: typ.Optional[str] = Depends(get_optional_current_user),
):
    async with get_db_connection() as db_session:
        comments = await articles_handler.get_article_comments(
            db_session, slug, curr_user_id=curr_user_id
        )

    return MultipleCommentsResponse(comments=comments)


@router.delete("/articles/{slug}/comments/{comment_id}")
async def delete_comment(
    slug: str,
    comment_id: str,
    user_id: str = Depends(get_current_user),
):
    async with get_db_connection() as db_session:
        await articles_handler.delete_article_comment(
            db_session, slug, comment_id, user_id
        )

    return {"message": "Comment deleted"}


#
# Favorites
#
@router.post("/articles/{slug}/favorite", response_model=SingleArticleResponse)
async def favorite_article(
    slug: str,
    user_id: str = Depends(get_current_user),
):
    async with get_db_connection() as db_session:
        article = await articles_handler.add_article_favorite(db_session, slug, user_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

    return SingleArticleResponse(article=article)


@router.delete("/articles/{slug}/favorite", response_model=SingleArticleResponse)
async def unfavorite_article(
    slug: str,
    user_id: str = Depends(get_current_user),
):
    async with get_db_connection() as db_session:
        article = await articles_handler.delete_article_favorite(
            db_session, slug, user_id
        )
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

    return SingleArticleResponse(article=article)
