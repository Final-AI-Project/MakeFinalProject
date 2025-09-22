from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Dict, Any


@dataclass
class MedicalDiagnosis:
    """aiomysql용 MedicalDiagnosis 모델 (기존 user_plant_pest 테이블 기반)"""
    idx: Optional[int] = None
    plant_id: Optional[int] = None
    pest_id: Optional[int] = None
    pest_date: Optional[date] = None
    plant_name: Optional[str] = None
    pest_name: Optional[str] = None
    symptom: Optional[str] = None
    cure: Optional[str] = None
    plant_species: Optional[str] = None
    meet_day: Optional[datetime] = None
    diagnosis_image_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MedicalDiagnosis":
        """딕셔너리에서 MedicalDiagnosis 객체 생성"""
        return cls(
            idx=data.get("idx"),
            plant_id=data.get("plant_id"),
            pest_id=data.get("pest_id"),
            pest_date=data.get("pest_date"),
            plant_name=data.get("plant_name"),
            pest_name=data.get("pest_name"),
            symptom=data.get("symptom"),
            cure=data.get("cure"),
            plant_species=data.get("plant_species"),
            meet_day=data.get("meet_day"),
            diagnosis_image_url=data.get("diagnosis_image_url"),
        )
