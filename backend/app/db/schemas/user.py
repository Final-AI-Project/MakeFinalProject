from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from .common import OrmBase

class UserCreate(OrmBase):
    user_id: str = Field(min_length=1, max_length=100)
    user_pw: str = Field(min_length=8, max_length=255)  # 평문 입력 → 서비스에서 해시
    email: EmailStr
    hp: str = Field(min_length=7, max_length=20)
    nickname: str = Field(min_length=1, max_length=20)

class UserUpdate(OrmBase):
    user_pw: str | None = Field(default=None, min_length=8, max_length=255)
    email: EmailStr | None = None
    hp: str | None = None
    nickname: str | None = None

# 비밀번호는 Create/Update에서만 다루고, 출력 스키마에는 포함하지 않음
class UserOut(OrmBase):
    idx: int
    user_id: str
    email: EmailStr
    hp: str
    nickname: str
    regdate: datetime | None

