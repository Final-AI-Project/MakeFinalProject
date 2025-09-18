from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

from core.config import get_settings
from utils.errors import http_error
from utils import token_blacklist  


# 비밀번호 해싱 및 검증
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


# 비밀번호 해싱
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# 비밀번호 검증
def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


# 현재 UTC 시간 반환
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# JWT 토큰 인코딩
def _encode_token(data: Dict[str,Any], expires_seconds: int) -> str:
    settings = get_settings()
    expire = _now_utc() + timedelta(seconds=expires_seconds)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "iat": _now_utc()})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


# 액세스 토큰 생성
def create_access_token(data: Dict[str, Any], expires_seconds: Optional[int] = None) -> str:
    """ 
     데이터는 반드시 sub:user_id(string)을 포함할 것
    """
    settings = get_settings()
    payload = {"type": "access", **data}
    # JWT 토큰 생성
    return _encode_token(payload, expires_seconds or settings.ACCESS_EXPIRES)


# 리프레시 토큰 생성
def create_refresh_token(data: Dict[str, Any], expires_seconds: Optional[int] = None) -> str:
    """
     데이터는 반드시 sub:user_id(string), jti:token_id(string)을 포함할 것
    """
    settings = get_settings()
    payload = {"type": "refresh", **data}
    # JWT 토큰 생성
    return _encode_token(payload, expires_seconds or settings.REFRESH_EXPIRES)


# JWT 토큰 디코딩
def decode_token(token: str, *, refresh: bool = False) -> Dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError:
        raise http_error("token_invalid", "토큰이 유효하지 않습니다.", 401)

    ttype = payload.get("type")
    if refresh and ttype != "refresh":
        raise http_error("token_type_invalid", "리프레시 토큰이 필요합니다.", 401)
    if not refresh and ttype != "access":
        raise http_error("token_type_invalid", "액세스 토큰이 필요합니다.", 401)

    # 리프레시 토큰 검증 (리프레시 토큰만 블랙리스트를 확인합니다)
    if refresh:
        jti = payload.get("jti")
        if not jti:
            raise http_error("token_invalid", "토큰이 유효하지 않습니다.", 401)
        if token_blacklist.contains(jti):
            raise http_error("token_revoked", "토큰이 취소되었습니다. 다시 로그인 해주세요.", 401)

    return payload


# 현재 사용자 정보 반환
async def get_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme), 
) -> Dict[str, Any]:
    
    if credentials is None or not credentials.scheme.lower() == "bearer":
        raise http_error("authorization_error", "인증 자격 증명이 제공되지 않았습니다.", 401)

    # 토큰 검증
    token = credentials.credentials
    payload = decode_token(token, refresh=False)
    user_id = payload.get("sub")
    if not user_id:
        raise http_error("token_invalid", "토큰이 유효하지 않습니다.", 401)
    
    user = storage.get_user_by_id(user_id)
    if not user:
        raise http_error("user_not_found", "사용자를 찾을 수 없습니다.", 404)
    
    return user
