from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date
from schemas.common import OrmBase


class DiseasePrediction(BaseModel):
    """병충해 예측 결과 스키마"""
    class_name: str = Field(..., description="병충해 이름")
    confidence: float = Field(..., description="신뢰도 (0.0 ~ 1.0)")
    rank: int = Field(..., description="순위")


class DiseaseDiagnosisResponse(BaseModel):
    """병충해 진단 응답 스키마"""
    success: bool = Field(..., description="진단 성공 여부")
    health_check: bool = Field(..., description="건강 상태 확인 여부")
    health_status: str = Field(..., description="건강 상태 (healthy/unhealthy/diseased)")
    health_confidence: float = Field(..., description="건강 상태 신뢰도")
    message: str = Field(..., description="진단 결과 메시지")
    recommendation: str = Field(..., description="권장사항")
    disease_predictions: List[DiseasePrediction] = Field(..., description="병충해 예측 결과")
    image_url: Optional[str] = Field(None, description="업로드된 이미지 URL")


class UserPlantOption(BaseModel):
    """사용자 식물 선택 옵션 스키마"""
    plant_id: int = Field(..., description="식물 ID")
    plant_name: str = Field(..., description="식물 별명")
    species: Optional[str] = Field(None, description="식물 종류")
    meet_day: Optional[date] = Field(None, description="만난 날")


class UserPlantsResponse(BaseModel):
    """사용자 식물 목록 응답 스키마"""
    plants: List[UserPlantOption] = Field(..., description="사용자 식물 목록")
    total_count: int = Field(..., description="총 식물 수")


class DiseaseDiagnosisSaveRequest(BaseModel):
    """병충해 진단 저장 요청 스키마"""
    plant_id: Optional[int] = Field(None, description="선택한 식물 ID (선택사항)")
    disease_name: str = Field(..., description="선택한 병충해 이름")
    confidence: float = Field(..., description="신뢰도")
    diagnosis_date: date = Field(..., description="진단 날짜")
    image_url: Optional[str] = Field(None, description="진단 이미지 URL")


class DiseaseDiagnosisSaveResponse(BaseModel):
    """병충해 진단 저장 응답 스키마"""
    success: bool = Field(..., description="저장 성공 여부")
    message: str = Field(..., description="저장 결과 메시지")
    diagnosis_id: Optional[int] = Field(None, description="저장된 진단 ID")
    saved_to_my_plants: bool = Field(..., description="내 식물에 저장되었는지 여부")
