from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from schemas.common import OrmBase


class MedicalDiagnosisListResponse(BaseModel):
    """병충해 진단 목록 응답 스키마 (기존 user_plant_pest 테이블 기반)"""
    idx: int = Field(..., description="진단 ID")
    plant_id: int = Field(..., description="식물 ID")
    pest_id: int = Field(..., description="병충해 ID")
    pest_date: date = Field(..., description="진단 날짜")
    plant_name: str = Field(..., description="식물 이름")
    pest_name: str = Field(..., description="병충해 이름")
    symptom: Optional[str] = Field(None, description="병충해 증상")
    cure: Optional[str] = Field(None, description="치료법")
    diagnosis_image_url: Optional[str] = Field(None, description="진단 시 찍은 사진 URL")


class MedicalDiagnosisDetailResponse(BaseModel):
    """병충해 진단 상세 응답 스키마"""
    idx: int = Field(..., description="진단 ID")
    plant_id: int = Field(..., description="식물 ID")
    pest_id: int = Field(..., description="병충해 ID")
    pest_date: date = Field(..., description="진단 날짜")
    plant_name: str = Field(..., description="식물 이름")
    plant_species: Optional[str] = Field(None, description="식물 종류")
    pest_name: str = Field(..., description="병충해 이름")
    symptom: Optional[str] = Field(None, description="병충해 증상")
    cure: Optional[str] = Field(None, description="치료법")
    meet_day: Optional[datetime] = Field(None, description="식물 만난 날")
    diagnosis_image_url: Optional[str] = Field(None, description="진단 시 찍은 사진 URL")
    related_diagnoses: Optional[List[MedicalDiagnosisListResponse]] = Field(None, description="관련 진단 기록")


class MedicalDiagnosisCreate(BaseModel):
    """병충해 진단 생성 스키마"""
    plant_id: int = Field(..., description="식물 ID")
    pest_id: int = Field(..., description="병충해 ID")
    pest_date: date = Field(..., description="진단 날짜")
    diagnosis_image_url: Optional[str] = Field(None, description="진단 시 찍은 사진 URL")


class MedicalDiagnosisUpdate(BaseModel):
    """병충해 진단 수정 스키마"""
    pest_id: Optional[int] = None
    pest_date: Optional[date] = None
    diagnosis_image_url: Optional[str] = None


class MedicalStatsResponse(BaseModel):
    """병충해 통계 응답 스키마"""
    total_diagnoses: int = Field(..., description="총 진단 수")
    active_plants: int = Field(..., description="진단받은 식물 수")
    most_common_pest: Optional[str] = Field(None, description="가장 흔한 병충해")
    recent_diagnoses: int = Field(..., description="최근 7일 진단 수")
