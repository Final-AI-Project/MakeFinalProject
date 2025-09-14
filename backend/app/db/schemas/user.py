from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from .common import OrmBase

class UserCreate(OrmBase):
    """회원가입용 스키마"""
    user_id: str = Field(min_length=1, max_length=100)
    user_pw: str = Field(min_length=8, max_length=255)  # 평문 입력 → 서비스에서 해시
    email: EmailStr
    hp: str = Field(min_length=7, max_length=20)
    nickname: str = Field(min_length=1, max_length=20)

class UserUpdate(OrmBase):
    """사용자 정보 수정용 스키마 (부분 갱신)"""
    user_pw: str | None = Field(default=None, min_length=8, max_length=255)
    email: EmailStr | None = None
    hp: str | None = None
    nickname: str | None = None

# 비밀번호는 Create/Update에서만 다루고, 출력 스키마에는 포함하지 않음
class UserOut(OrmBase):
    """출력용 User 스키마 (비밀번호 제외)"""
    idx: int
    user_id: str
    email: EmailStr
    hp: str
    nickname: str
    regdate: datetime | None


class UserLoginRequest(BaseModel):
    """로그인 요청 바디"""
    id_or_email: str = Field(..., description="사용자 ID 또는 이메일", examples=["user123", "user@example.com"])
    password: str = Field(..., min_length=8, max_length=255, description="비밀번호", examples=["Passw0rd!"])

class TokenPair(BaseModel):
    """로그인/리프레시 성공 시 내려주는 토큰 페어"""
    token_type: str = Field("bearer", description="토큰 타입 (항상 'bearer')")
    access_token: str = Field(..., description="액세스 토큰 (JWT)")
    refresh_token: str = Field(..., description="리프레시 토큰 (JWT)")
    expires_in: int = Field(..., description="액세스 토큰 만료(초)")

class RefreshRequest(BaseModel):
    """리프레시 요청 바디"""
    refresh_token: str = Field(..., description="리프레시 토큰(JWT)")

class LogoutRequest(BaseModel):
    """로그아웃 요청 바디 (서버 측에서는 refresh_token의 jti를 블랙리스트에 올림)"""
    refresh_token: str = Field(..., description="리프레시 토큰(JWT)")    