from flask import Blueprint, request
from realworld.api.core.db import run_with_db
import realworld.api.routes.v1.articles.handler as articles_handler
from realworld.api.core.auth import validate_token, get_user_id_from_token
from realworld.api.routes.v1.articles.models import (
    # GetArticlesQueryParams,
    # GetFeedQueryParams,
    GetTagsResponse,
    CreateArticleRequest,
    UpdateArticleRequest,
    CreateCommentRequest,
    CreateCommentResponse,
    SingleArticleResponse,
    MultipleArticlesResponse,
    MultipleCommentsResponse,
)


articles_blueprint = Blueprint("articles_endpoints", __name__)
tags_blueprint = Blueprint("tags_endpoints", __name__, url_prefix="/tags")


@articles_blueprint.route("/articles", methods=["GET"])
def get_articles() -> dict:
    """
    Returns most recent articles globally by default, provide tag, author or favorited query parameter to filter results
    """
    user_id = get_user_id_from_token()
    articles = run_with_db(
        articles_handler.get_articles,
        curr_user_id=user_id,
        filter_tag=request.args.get("tag"),
        author_username_filter=request.args.get("author"),
        favorited_by_username_filter=request.args.get("favorited"),
        limit=int(request.args.get("limit", 20)),
        offset=int(request.args.get("offset", 0)),
    )

    return MultipleArticlesResponse(
        articles=articles,
        articles_count=len(articles),
    ).model_dump()


@validate_token
@articles_blueprint.route("/articles/feed", methods=["GET"])
def get_feed() -> dict:
    """
    Returns articles created by followed users, ordered by most recent first.
    """
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    articles = run_with_db(
        articles_handler.get_feed_articles,
        user_id,
        limit=int(request.args.get("limit", 20)),
        offset=int(request.args.get("offset", 0)),
    )

    return MultipleArticlesResponse(
        articles=articles,
        articles_count=len(articles),
    ).model_dump()


@articles_blueprint.route("/articles/<string:slug>", methods=["GET"])
def get_article(slug: str) -> dict:
    article = run_with_db(
        articles_handler.get_article_by_slug,
        slug,
        curr_user_id=get_user_id_from_token(),
    )
    if not article:
        return {"message": "Article not found"}, 404

    return SingleArticleResponse(article=article).model_dump()


@articles_blueprint.route("/articles", methods=["POST"])
def create_article() -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    data = CreateArticleRequest.model_validate(request.json)
    article = run_with_db(articles_handler.create_article, user_id, data.article)

    return SingleArticleResponse(article=article).model_dump()


@articles_blueprint.route("/articles/<string:slug>", methods=["PUT"])
def update_article(slug) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    data = UpdateArticleRequest.model_validate(request.json)
    article = run_with_db(articles_handler.update_article, slug, user_id, data.article)
    if not article:
        return {"message": "Article not found"}, 404

    return SingleArticleResponse(article=article).model_dump()


@articles_blueprint.route("/articles/<string:slug>", methods=["DELETE"])
def delete_article(slug: str) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    if not run_with_db(articles_handler.delete_article, slug, user_id):
        return {"message": "Article not found"}, 404

    return {"message": "Article deleted"}


#
# Comments
#
@articles_blueprint.route("/articles/<string:slug>/comments", methods=["POST"])
def create_comment(slug: str) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    data = CreateCommentRequest.model_validate(request.json)

    does_article_exist, comment = run_with_db(
        articles_handler.create_article_comment, slug, user_id, data.comment
    )
    if not does_article_exist:
        return {"message": "Article not found"}, 404

    return CreateCommentResponse(comment=comment).model_dump()


@articles_blueprint.route("/articles/<string:slug>/comments", methods=["GET"])
def get_comments(slug: str) -> dict:
    comments = run_with_db(
        articles_handler.get_article_comments,
        slug,
        curr_user_id=get_user_id_from_token(),
    )

    return MultipleCommentsResponse(comments=comments).model_dump()


@articles_blueprint.route(
    "/articles/<string:slug>/comments/<string:comment_id>", methods=["DELETE"]
)
def delete_comment(slug: str, comment_id: str) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    run_with_db(articles_handler.delete_article_comment, slug, comment_id, user_id)

    return {"message": "Comment deleted"}


#
# Favorites
#
@articles_blueprint.route("/articles/<string:slug>/favorite", methods=["POST"])
def favorite_article(slug: str) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    article = run_with_db(articles_handler.add_article_favorite, slug, user_id)
    if not article:
        return {"message": "Article not found"}, 404

    return SingleArticleResponse(article=article).model_dump()


@articles_blueprint.route("/articles/<string:slug>/favorite", methods=["DELETE"])
def unfavorite_article(slug: str) -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"message": "Invalid token"}, 401

    article = run_with_db(articles_handler.delete_article_favorite, slug, user_id)
    if not article:
        return {"message": "Article not found"}, 404

    return SingleArticleResponse(article=article).model_dump()


#
# Tags
#
@tags_blueprint.route("", methods=["GET"])
def get_tags() -> dict:
    tags = run_with_db(articles_handler.get_all_tags)

    return GetTagsResponse(tags=tags).model_dump()
