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

# 일기 목록 페이지용 스키마
class DiaryListItemResponse(OrmBase):
    """일기 목록 아이템 응답 스키마"""
    idx: int
    user_title: str
    user_content: str
    plant_nickname: Optional[str] = None
    plant_species: Optional[str] = None
    plant_reply: Optional[str] = None
    weather: Optional[str] = None
    weather_icon: Optional[str] = None
    img_url: Optional[str] = None
    hashtag: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DiaryListResponse(OrmBase):
    """일기 목록 응답 스키마"""
    diaries: List[DiaryListItemResponse]
    total_count: int
    page: int
    limit: int
    has_more: bool

class DiarySearchRequest(OrmBase):
    """일기 검색 요청 스키마"""
    query: Optional[str] = None
    plant_nickname: Optional[str] = None
    plant_species: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hashtag: Optional[str] = None

class DiaryStatsResponse(OrmBase):
    """일기 통계 응답 스키마"""
    total_diaries: int
    total_plants: int
    recent_diary_count: int  # 최근 7일
    most_active_plant: Optional[str] = None
    average_diaries_per_plant: float

# 일기 작성/수정용 스키마
class DiaryWriteRequest(OrmBase):
    """일기 작성 요청"""
    user_title: str = Field(min_length=1, max_length=200)
    user_content: str = Field(min_length=1)
    plant_nickname: str | None = Field(None, max_length=100)
    plant_species: str | None = Field(None, max_length=100)
    hashtag: str | None = None
    weather: str | None = None

class DiaryWriteResponse(OrmBase):
    """일기 작성/수정 응답"""
    success: bool
    message: str
    diary: DiaryListItemResponse
