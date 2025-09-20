from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date
from schemas.common import OrmBase


class DiseasePrediction(BaseModel):
    """병충해 예측 결과 스키마"""
    disease_name: str = Field(..., description="병충해 이름")
    confidence: float = Field(..., description="신뢰도 (0.0 ~ 1.0)")
    description: str = Field(..., description="병충해 설명")
    treatment: str = Field(..., description="치료법")
    prevention: str = Field(..., description="예방법")


class DiseaseDiagnosisResponse(BaseModel):
    """병충해 진단 응답 스키마"""
    success: bool = Field(..., description="진단 성공 여부")
    message: str = Field(..., description="진단 결과 메시지")
    predictions: List[DiseasePrediction] = Field(..., description="상위 3개 예측 결과")
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
    predictions: List[DiseasePrediction] = Field(..., description="진단 결과 목록")
    image_url: Optional[str] = Field(None, description="진단 이미지 URL")
    notes: Optional[str] = Field(None, description="추가 메모")


class DiseaseDiagnosisSaveResponse(BaseModel):
    """병충해 진단 저장 응답 스키마"""
    success: bool = Field(..., description="저장 성공 여부")
    message: str = Field(..., description="저장 결과 메시지")
    diagnosis_id: Optional[int] = Field(None, description="저장된 진단 ID")
