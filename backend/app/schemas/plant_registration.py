from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

class PlantRegistrationRequest(BaseModel):
    """식물 등록 요청 스키마"""
    plant_name: str = Field(..., min_length=1, max_length=100, description="식물 별명")
    species: Optional[str] = Field(None, max_length=100, description="식물 품종")
    meet_day: date = Field(..., description="키우기 시작한 날")
    plant_id: Optional[int] = Field(None, description="식물 위키 ID (선택사항)")

class PlantRegistrationResponse(BaseModel):
    """식물 등록 응답 스키마"""
    idx: int = Field(..., description="등록된 식물 ID")
    user_id: str = Field(..., description="사용자 ID")
    plant_name: str = Field(..., description="식물 별명")
    species: Optional[str] = Field(None, description="식물 품종")
    meet_day: date = Field(..., description="키우기 시작한 날")
    plant_id: Optional[int] = Field(None, description="식물 위키 ID")
    created_at: datetime = Field(..., description="등록일시")

class SpeciesClassificationRequest(BaseModel):
    """품종 분류 요청 스키마"""
    image_url: str = Field(..., description="분류할 이미지 URL")

class SpeciesClassificationResponse(BaseModel):
    """품종 분류 응답 스키마"""
    success: bool = Field(..., description="분류 성공 여부")
    species: Optional[str] = Field(None, description="분류된 품종명 (영어)")
    species_korean: Optional[str] = Field(None, description="분류된 품종명 (한글)")
    confidence: Optional[float] = Field(None, description="신뢰도 (0-1)")
    top_predictions: Optional[List[dict]] = Field(None, description="상위 예측 결과들")
    message: str = Field(..., description="결과 메시지")

class PlantListResponse(BaseModel):
    """식물 목록 응답 스키마"""
    plants: List[PlantRegistrationResponse]
    total_count: int
    page: int
    limit: int
    has_more: bool

class PlantUpdateRequest(BaseModel):
    """식물 정보 수정 요청 스키마"""
    plant_name: Optional[str] = Field(None, min_length=1, max_length=100, description="식물 별명")
    species: Optional[str] = Field(None, max_length=100, description="식물 품종")
    meet_day: Optional[date] = Field(None, description="키우기 시작한 날")
    plant_id: Optional[int] = Field(None, description="식물 위키 ID")

class PlantUpdateResponse(BaseModel):
    """식물 정보 수정 응답 스키마"""
    idx: int = Field(..., description="식물 ID")
    user_id: str = Field(..., description="사용자 ID")
    plant_name: str = Field(..., description="식물 별명")
    species: Optional[str] = Field(None, description="식물 품종")
    meet_day: date = Field(..., description="키우기 시작한 날")
    plant_id: Optional[int] = Field(None, description="식물 위키 ID")
    updated_at: datetime = Field(..., description="수정일시")
