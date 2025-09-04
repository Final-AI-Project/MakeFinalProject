from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import settings
from ..services.storage import new_uuid
from .token_blacklist import contains

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def _create_token(data: Dict[str, Any], expires_seconds: int, token_type: str) -> str:
    to_encode = data.copy()
    to_encode.update(
        {
            "exp": datetime.utcnow() + timedelta(seconds=expires_seconds),
            "jti": new_uuid(),
            "token_type": token_type,
        }
    )
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_access_token(data: Dict[str, Any], expires_seconds: int) -> str:
    return _create_token(data, expires_seconds, "access")


def create_refresh_token(data: Dict[str, Any], expires_seconds: int) -> str:
    return _create_token(data, expires_seconds, "refresh")


def decode_token(token: str, *, refresh: bool = False) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        token_type = payload.get("token_type")
        if refresh:
            if token_type != "refresh" or contains(payload.get("jti")):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        else:
            if token_type != "access":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    payload = decode_token(credentials.credentials)
    from ..services import users_service

    user_id = payload.get("sub")
    return users_service.get_me(user_id)
