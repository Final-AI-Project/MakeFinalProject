from ..config import settings
from ..utils.errors import http_error
from ..utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from ..utils import token_blacklist
from .storage import users, new_uuid, utcnow_iso


def _user_public(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "nickname": user["nickname"],
        "avatar_url": user.get("avatar_url"),
        "created_at": user["created_at"],
    }


def register(email: str, password: str, nickname: str) -> dict:
    for u in users.values():
        if u["email"] == email:
            raise http_error("EMAIL_EXISTS", "email already registered", 400)
    user_id = new_uuid()
    user = {
        "id": user_id,
        "email": email,
        "password": hash_password(password),
        "nickname": nickname,
        "avatar_url": None,
        "created_at": utcnow_iso(),
    }
    users[user_id] = user
    return _user_public(user)


def login(email: str, password: str) -> dict:
    user = next((u for u in users.values() if u["email"] == email), None)
    if not user or not verify_password(password, user["password"]):
        raise http_error("INVALID_CREDENTIALS", "invalid credentials", 401)
    access = create_access_token({"sub": user["id"]}, settings.ACCESS_EXPIRES)
    refresh = create_refresh_token({"sub": user["id"]}, settings.REFRESH_EXPIRES)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": _user_public(user),
    }


def refresh(refresh_token: str) -> dict:
    payload = decode_token(refresh_token, refresh=True)
    user_id = payload.get("sub")
    access = create_access_token({"sub": user_id}, settings.ACCESS_EXPIRES)
    return {"access_token": access, "token_type": "bearer"}


def logout(refresh_token: str) -> None:
    payload = decode_token(refresh_token, refresh=True)
    token_blacklist.add(payload.get("jti"))
