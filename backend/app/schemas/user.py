from __future__ import annotations

from datetime import datetime
from pydantic import Field
from .common import OrmBase


class UserCreate(OrmBase):
    user_id: str = Field(min_length=1, max_length=100)
    user_pw: str = Field(min_length=8, max_length=100)
    email: str = Field(max_length=50)
    hp: str = Field(max_length=20)
    nickname: str = Field(min_length=1, max_length=20)


class UserUpdate(OrmBase):
    user_pw: str | None = None
    email: str | None = None
    hp: str | None = None
    nickname: str | None = None


class UserOut(OrmBase):
    idx: int
    user_id: str
    email: str
    hp: str
    nickname: str
    regdate: datetime | None


class UserLoginRequest(OrmBase):
    id_or_email: str = Field(description="사용자 ID 또는 이메일")
    password: str = Field(description="비밀번호")


class TokenPair(OrmBase):
    access_token: str
    refresh_token: str


class RefreshRequest(OrmBase):
    refresh_token: str


class LogoutRequest(OrmBase):
    refresh_token: str
