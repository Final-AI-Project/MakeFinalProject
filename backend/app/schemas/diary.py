from __future__ import annotations
from datetime import datetime
from pydantic import Field
from typing import List, Optional
from .common import OrmBase
from .img_address import ImgAddressOut

class DiaryCreate(OrmBase):
    user_id: str = Field(min_length=1, max_length=100)
    user_title: str = Field(min_length=1, max_length=200)
    img_url: str | None = None
    user_content: str = Field(min_length=1)
    hashtag: str | None = None
    plant_content: str | None = None
    weather: str | None = None

class DiaryUpdate(OrmBase):
    user_title: str | None = None
    img_url: str | None = None
    user_content: str | None = None
    hashtag: str | None = None
    plant_content: str | None = None
    weather: str | None = None

class DiaryOut(OrmBase):
    idx: int
    user_id: str
    user_title: str
    img_url: str | None
    user_content: str
    hashtag: str | None
    plant_content: str | None
    weather: str | None
    created_at: datetime

    # 관계 포함
    images: List[ImgAddressOut] = []

class DiaryListOut(OrmBase):
    items: List[DiaryOut]
    next_cursor: str | None
    has_more: bool
    total_count: int
