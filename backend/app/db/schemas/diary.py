from __future__ import annotations

from datetime import datetime
from pydantic import Field
from .common import OrmBase
from .img_address import ImgAddressOut

class DiaryCreate(OrmBase):
    user_id: str = Field(min_length=1, max_length=100)
    user_title: str = Field(min_length=1, max_length=500)
    img_url: str | None = None
    user_content: str | None = None
    hashtag: str | None = None
    plant_content: str | None = None
    weather: str | None = Field(default=None, max_length=10)
    created_at: datetime | None = None  # 서버에서 now() 채우는 것도 가능

class DiaryUpdate(OrmBase):
    user_title: str | None = None
    img_url: str | None = None
    user_content: str | None = None
    hashtag: str | None = None
    plant_content: str | None = None
    weather: str | None = None

class DiaryOut(OrmBase):
    diary_id: int
    user_id: str
    user_title: str
    img_url: str | None
    user_content: str | None
    hashtag: str | None
    plant_content: str | None
    weather: str | None
    created_at: datetime | None

    # 관계 포함 응답 (선택)
    images: list[ImgAddressOut] = []

