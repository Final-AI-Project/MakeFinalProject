from typing import Dict, Any, Optional

from backend.app.core.config import get_settings
from backend.app.services import storage
from backend.app.utils import token_blacklist
from backend.app.utils.errors import http_error
from backend.app.utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from uuid import uuid4


def register(email: str, password: str, nickname: str) -> Dict[str, Any]:
    if storage.get_user_by_email(email):
        raise http_error("EMAIL_IN_USE", "email already registered", status=409)

    now = storage.utcnow_iso()
    user = {
        "id": storage.new_uuid(),
        "email": email,
        "nickname": nickname,
        "avatar_url": None,
        "password_hash": hash_password(password),
        "created_at": now,
        "updated_at": now,
    }
    storage.add_user(user)
    return _public_user(user)


def login(email: str, password: str) -> Dict[str, Any]:
    user = storage.get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise http_error("INVALID_CREDENTIALS", "invalid email or password", status=401)

    tokens = _issue_tokens_for_user(user["id"])
    return {"user": _public_user(user), **tokens}


def refresh(refresh_token: str) -> Dict[str, Any]:
    # decode+validate inside utils.security.decode_token(), blacklist checked by services flow
    from backend.app.utils.security import decode_token

    payload = decode_token(refresh_token, refresh=True)
    jti = payload["jti"]
    sub = payload["sub"]

    # Double-check blacklist here (decode already checked)
    if token_blacklist.contains(jti):
        raise http_error("TOKEN_REVOKED", "refresh token is revoked", status=401)

    settings = get_settings()
    access = create_access_token({"sub": sub}, expires_seconds=settings.ACCESS_EXPIRES)
    return {"access_token": access, "token_type": "bearer"}


def logout(refresh_token: str) -> Dict[str, Any]:
    from backend.app.utils.security import decode_token

    payload = decode_token(refresh_token, refresh=True)
    jti = payload["jti"]
    token_blacklist.add(jti)
    return {"ok": True}


def _issue_tokens_for_user(user_id: str) -> Dict[str, str]:
    settings = get_settings()
    access = create_access_token({"sub": user_id}, expires_seconds=settings.ACCESS_EXPIRES)
    refresh = create_refresh_token({"sub": user_id, "jti": str(uuid4())}, expires_seconds=settings.REFRESH_EXPIRES)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def _public_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": user["id"],
        "email": user["email"],
        "nickname": user.get("nickname"),
        "avatar_url": user.get("avatar_url"),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }
