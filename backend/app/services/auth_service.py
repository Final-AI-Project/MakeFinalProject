from __future__ import annotations

import uuid
from typing import Optional, Tuple, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from db.models.user import User
from db.schemas.user import UserCreate
from db.crud import user as users_crud

from utils.errors import http_error
from utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from core.config import get_settings
from utils import token_blacklist


def _normalize_email(email: str) -> str:
    return email.strip().casefold()  # 대소문자/공백 정규화

def _normalize_hp(hp: str) -> str:
    # 숫자만 남겨 중복 판단 일관화(010-1234-5678 → 01012345678)
    return "".join(ch for ch in hp if ch.isdigit())


# --------------------
    # 회원가입 서비스
# --------------------
async def register_user(*, db: AsyncSession, payload: UserCreate) -> User:
    """
    회원가입 서비스:
    - 입력 정규화(user_id/email/hp)
    - 중복 검사(user_id, email, hp) → 충돌 시 http_error(...) 409
    - 비밀번호 해싱 → 저장
    - flush() 까지만 수행 (commit은 라우터의 get_db 의존성이 처리)
    - 성공 시 User ORM 객체 반환
    """
    user_id = payload.user_id.strip()
    email = _normalize_email(payload.email)
    hp = _normalize_hp(payload.hp)
    nickname = payload.nickname.strip()

    # --- 사전 중복 검사 ---
    # user_id
    if await users_crud.get_by_user_id(db, user_id):
        raise http_error("user_id_conflict", "이미 사용 중인 사용자 ID입니다.", 409)

    # email
    if await users_crud.get_by_email(db, email):
        raise http_error("email_conflict", "이미 사용 중인 이메일입니다.", 409)

    # hp
    res = await db.execute(select(User).where(User.hp == hp))
    if res.scalar_one_or_none():
        raise http_error("hp_conflict", "이미 사용 중인 휴대폰 번호입니다.", 409)

    # --- 비밀번호 해시 ---
    pw_hash = hash_password(payload.user_pw)

    # --- 생성 ---
    try:
        user = await users_crud.create(
            db,
            user_id=user_id,
            hashed_pw=pw_hash,
            email=email,
            hp=hp,
            nickname=nickname,
        )
        return user

    except IntegrityError as e:
        # 경합 상황(동시에 가입 시도 등)에서 DB 유니크 제약 위반 방어
        # 원문 메시지로 어떤 컬럼인지 추정해서 사용자 친화 메시지로 변환
        msg = (str(e.orig) if getattr(e, "orig", None) else "").lower()
        if "user_id" in msg:
            raise http_error("user_id_conflict", "이미 사용 중인 사용자 ID입니다.", 409)
        if "email" in msg:
            raise http_error("email_conflict", "이미 사용 중인 이메일입니다.", 409)
        if "hp" in msg:
            raise http_error("hp_conflict", "이미 사용 중인 휴대폰 번호입니다.", 409)
        # 어떤 컬럼인지 특정 불가 → 일반 충돌로 응답
        raise http_error("unique_violation", "중복된 값이 존재합니다.", 409)


# --------------------
    # 토큰 유틸
# --------------------
def _new_jti() -> str:
    return str(uuid.uuid4())

def _access_claims(user: User) -> Dict[str, Any]:
    # 최소한 sub(=user_id)는 반드시 포함 (security.create_access_token 주석 요구사항)
    return {
        "sub": user.user_id,
        "uid": user.idx,          # 편의용: 내부 식별자
        "nickname": user.nickname # 필요 없다면 제거 가능
    }

def _refresh_claims(user: User, jti: str) -> Dict[str, Any]:
    # refresh에는 jti가 필수 (security.decode_token에서 블랙리스트 검증)
    return {
        "sub": user.user_id,
        "uid": user.idx,
        "jti": jti,
    }

def _issue_token_pair(user: User) -> Dict[str, Any]:
    """
    액세스/리프레시 토큰을 한 번에 발급.
    - access: {"type":"access", sub, ...}
    - refresh: {"type":"refresh", sub, jti, ...}
    반환: {"token_type":"bearer", "access_token":..., "refresh_token":..., "expires_in":seconds}
    """
    settings = get_settings()
    access = create_access_token(_access_claims(user))
    jti = _new_jti()
    refresh = create_refresh_token(_refresh_claims(user, jti))
    return {
        "token_type": "bearer",
        "access_token": access,
        "refresh_token": refresh,
        "expires_in": settings.ACCESS_EXPIRES,
    }


# --------------------
    # 로그인 / 리프레시 / 로그아웃
# --------------------
async def login(db: AsyncSession, *, user_id_or_email: str, password: str) -> Dict[str, Any]:
    """
    - user_id 또는 email 로 사용자 조회
    - 비밀번호 검증 실패 시 401
    - 성공 시 토큰 페어 발급
    """
    identifier = user_id_or_email.strip()
    user: Optional[User] = await users_crud.get_by_user_id(db, identifier)
    if not user:
        # email일 수도 있음
        user = await users_crud.get_by_email(db, _normalize_email(identifier))

    if not user:
        raise http_error("invalid_credentials", "아이디(또는 이메일) 또는 비밀번호가 올바르지 않습니다.", 401)

    if not verify_password(password, user.user_pw):
        raise http_error("invalid_credentials", "아이디(또는 이메일) 또는 비밀번호가 올바르지 않습니다.", 401)

    return _issue_token_pair(user)


async def refresh_tokens(db: AsyncSession, *, refresh_token: str) -> Dict[str, Any]:
    """
    - 리프레시 토큰 검증(유효성/타입/블랙리스트) → payload 획득
    - 사용자 존재 확인
    - (권장) 토큰 회전: 기존 jti 블랙리스트에 등록 → 새로운 리프레시/액세스 발급
    """
    payload = decode_token(refresh_token, refresh=True)  # 유효성/블랙리스트 검사 수행
    sub = payload.get("sub")
    jti = payload.get("jti")
    if not sub or not jti:
        raise http_error("token_invalid", "토큰이 유효하지 않습니다.", 401)

    # 사용자 확인
    user = await users_crud.get_by_user_id(db, sub)
    if not user:
        raise http_error("user_not_found", "사용자를 찾을 수 없습니다.", 404)

    # 기존 jti를 블랙리스트에 추가하고 새 jti로 refresh 재발급
    try:
        token_blacklist.add(jti)  
    except Exception:
        raise http_error("token_rotation_failed", "토큰 재발급 중 오류가 발생했습니다.", 500)

    return _issue_token_pair(user)


async def logout(*, refresh_token: str) -> None:
    """
    - 리프레시 토큰의 jti를 블랙리스트에 등록 → 이후 사용 불가
    - 액세스 토큰은 클라이언트 측에서 폐기
    """
    payload = decode_token(refresh_token, refresh=True)
    jti = payload.get("jti")
    if not jti:
        raise http_error("token_invalid", "토큰이 유효하지 않습니다.", 401)

    try:
        token_blacklist.add(jti)
    except Exception:
        raise http_error("logout_failed", "로그아웃 처리 중 오류가 발생했습니다.", 500)

# ----------------------------
#   내 정보(me) 조회 헬퍼
# ----------------------------
async def get_user_for_sub(db: AsyncSession, *, sub: str) -> User:
    """
    access 토큰의 sub(user_id)로 사용자 조회.
    라우터에서 security.get_current_user를 쓰지 않고 DB를 직조회하고 싶을 때 사용.
    """
    user = await users_crud.get_by_user_id(db, sub)
    if not user:
        raise http_error("user_not_found", "사용자를 찾을 수 없습니다.", 404)
    return user