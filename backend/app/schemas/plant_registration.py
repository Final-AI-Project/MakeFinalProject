from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional
from pydantic import Field, BaseModel
from .common import OrmBase

class SpeciesClassificationRequest(OrmBase):
    """품종 분류 요청"""
    image_url: str = Field(..., description="분류할 식물 이미지 URL")

class SpeciesClassificationResult(OrmBase):
    """품종 분류 결과"""
    species: str = Field(..., description="분류된 식물 종류")
    confidence: float = Field(..., ge=0, le=1, description="분류 신뢰도 (0-1)")
    is_success: bool = Field(..., description="분류 성공 여부")
    message: str | None = Field(None, description="분류 실패 시 메시지")

class PlantRegistrationCreate(OrmBase):
    """식물 등록 요청"""
    # 품종 분류 결과 (성공 시)
    species: str | None = Field(None, description="분류된 식물 종류")
    
    # 사용자 입력 정보
    plant_name: str = Field(..., min_length=1, max_length=100, description="식물 별명")
    meet_day: date = Field(..., description="키우기 시작한 날")
    location: str = Field(..., min_length=1, max_length=200, description="키우는 위치")
    is_indoor: bool = Field(..., description="실내/실외 여부")
    
    # 품종 분류에 사용된 이미지 정보
    classification_image_url: str = Field(..., description="품종 분류에 사용된 이미지 URL")
    
    # 추가 정보 (선택사항)
    notes: str | None = Field(None, description="추가 메모")

class PlantRegistrationOut(OrmBase):
    """식물 등록 응답"""
    plant_id: int = Field(..., description="등록된 식물 ID")
    plant_name: str = Field(..., description="식물 별명")
    species: str | None = Field(None, description="식물 종류")
    meet_day: date = Field(..., description="키우기 시작한 날")
    location: str = Field(..., description="키우는 위치")
    is_indoor: bool = Field(..., description="실내/실외 여부")
    profile_image_url: str | None = Field(None, description="식물 프로필 이미지 URL")
    notes: str | None = Field(None, description="추가 메모")
    created_at: datetime = Field(..., description="등록일시")

class PlantRegistrationUpdate(OrmBase):
    """식물 정보 수정"""
    plant_name: str | None = Field(None, min_length=1, max_length=100)
    species: str | None = Field(None)
    meet_day: date | None = None
    location: str | None = Field(None, min_length=1, max_length=200)
    is_indoor: bool | None = None
    notes: str | None = None

class PlantRegistrationListOut(OrmBase):
    """식물 등록 목록 응답"""
    items: List[PlantRegistrationOut]
    next_cursor: str | None
    has_more: bool
    total_count: int
