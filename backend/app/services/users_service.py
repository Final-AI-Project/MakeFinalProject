from .storage import users
from ..utils.errors import http_error


def get_me(user_id: str) -> dict:
    user = users.get(user_id)
    if not user:
        raise http_error("RESOURCE_NOT_FOUND", "user not found", 404)
    return {
        "id": user["id"],
        "email": user["email"],
        "nickname": user["nickname"],
        "avatar_url": user.get("avatar_url"),
        "created_at": user["created_at"],
    }


def patch_me(user_id: str, nickname: str | None = None, avatar_url: str | None = None) -> dict:
    user = users.get(user_id)
    if not user:
        raise http_error("RESOURCE_NOT_FOUND", "user not found", 404)
    if nickname is not None:
        user["nickname"] = nickname
    if avatar_url is not None:
        user["avatar_url"] = avatar_url
    return get_me(user_id)
