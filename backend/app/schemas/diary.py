from __future__ import annotations
from datetime import datetime
from pydantic import Field
from typing import List, Optional
from .common import OrmBase

# 간단한 이미지 주소 스키마 (img_address.py가 삭제되어 직접 정의)
class ImgAddressOut(OrmBase):
    idx: int
    img_url: str
    created_at: datetime

class DiaryCreate(OrmBase):
    user_id: str = Field(min_length=1, max_length=100)
    user_title: str = Field(min_length=1, max_length=200)
    img_url: str | None = None
    user_content: str = Field(min_length=1)
    hashtag: str | None = None
    plant_nickname: str | None = Field(None, max_length=100)  # 식물별명
    plant_species: str | None = Field(None, max_length=100)   # 식물종류
    plant_reply: str | None = None     # 식물의 답변 (자동생성)
    weather: str | None = None
    weather_icon: str | None = None    # 날씨 아이콘 URL

class DiaryUpdate(OrmBase):
    user_title: str | None = None
    img_url: str | None = None
    user_content: str | None = None
    hashtag: str | None = None
    plant_nickname: str | None = Field(None, max_length=100)
    plant_species: str | None = Field(None, max_length=100)
    plant_reply: str | None = None  # 수정시 재생성
    weather: str | None = None
    weather_icon: str | None = None

class DiaryOut(OrmBase):
    idx: int
    user_id: str
    user_title: str
    img_url: str | None
    user_content: str
    hashtag: str | None
    plant_nickname: str | None
    plant_species: str | None
    plant_reply: str | None
    weather: str | None
    weather_icon: str | None
    created_at: datetime
    updated_at: datetime | None

    # 관계 포함
    images: List[ImgAddressOut] = []

class DiaryListOut(OrmBase):
    items: List[DiaryOut]
    next_cursor: str | None
    has_more: bool
    total_count: int

# 일기 작성/수정용 스키마
class DiaryWriteRequest(OrmBase):
    """일기 작성 요청"""
    user_title: str = Field(min_length=1, max_length=200)
    user_content: str = Field(min_length=1)
    plant_nickname: str | None = Field(None, max_length=100)
    plant_species: str | None = Field(None, max_length=100)
    hashtag: str | None = None

class DiaryWriteResponse(OrmBase):
    """일기 작성/수정 응답"""
    idx: int
    user_title: str
    user_content: str
    plant_nickname: str | None
    plant_species: str | None
    plant_reply: str | None
    weather: str | None
    weather_icon: str | None
    img_url: str | None
    created_at: datetime
    updated_at: datetime | None
