from flask import Blueprint, request
from realworld.api.core.db import run_with_db
from realworld.api.core.auth import generate_jwt, validate_token, get_user_id_from_token
from realworld.api.routes.v1.users import handler as users_handler
from realworld.api.routes.v1.users.models import (
    RegisterUserRequest,
    UpdateUserRequest,
    LoginUserRequest,
    AuthUser,
    AuthUserResponse,
)


users_blueprint = Blueprint(
    "users_endpoints",
    __name__,
)


@users_blueprint.route("/users", methods=["POST"])
def create_user() -> dict:
    data = RegisterUserRequest.model_validate(request.json)
    if not (user := run_with_db(users_handler.create_user, data.user)):
        return {"error": "A user with this username already exists."}, 409

    return AuthUserResponse(
        user=AuthUser(
            email=user.email,
            token=generate_jwt(user.user_id),
            username=user.username,
            bio=user.bio,
            image=user.image,
        )
    ).model_dump()


@users_blueprint.route("/users/login", methods=["POST"])
def authenticate_user() -> dict:
    data = LoginUserRequest.model_validate(request.json)
    if not (
        user := run_with_db(
            users_handler.validate_user_creds,
            email=data.user.email,
            password=data.user.password,
        )
    ):
        return {"error": "User does not exist."}, 404

    return AuthUserResponse(
        user=AuthUser(
            email=user.email,
            token=generate_jwt(user.user_id),
            username=user.username,
            bio=user.bio,
            image=user.image,
        )
    ).model_dump()


@validate_token
@users_blueprint.route("/user", methods=["GET"])
def get_current_user() -> dict:
    if not (user_id := get_user_id_from_token()):
        return {"error": "Invalid token."}, 401

    if user := run_with_db(users_handler.get_user, user_id):
        return AuthUserResponse(
            user=AuthUser(
                email=user.email,
                token=generate_jwt(user_id),
                username=user.username,
                bio=user.bio,
                image=user.image,
            )
        ).model_dump()

    return {"error": "User does not exist."}, 404


@validate_token
@users_blueprint.route("/user", methods=["PUT"])
def update_user() -> dict:
    data = UpdateUserRequest.model_validate(request.json)
    if not (user_id := get_user_id_from_token()):
        return {"error": "Invalid token."}, 401

    if not (user := run_with_db(users_handler.update_user, user_id, data.user)):
        return {"error": "User does not exist."}, 404

    return AuthUserResponse(
        user=AuthUser(
            email=user.email,
            token=generate_jwt(user_id),
            username=user.username,
            bio=user.bio,
            image=user.image,
        )
    ).model_dump()
