from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class UserPlant:
    """aiomysql용 UserPlant 모델"""
    idx: Optional[int] = None
    user_id: str = ""
    plant_id: int = 0
    plant_name: str = ""
    species: Optional[str] = None
    pest_id: Optional[int] = None
    meet_day: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPlant":
        """딕셔너리에서 UserPlant 객체 생성"""
        return cls(
            idx=data.get("idx"),
            user_id=data.get("user_id", ""),
            plant_id=data.get("plant_id", 0),
            plant_name=data.get("plant_name", ""),
            species=data.get("species"),
            pest_id=data.get("pest_id"),
            meet_day=data.get("meet_day"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """UserPlant 객체를 딕셔너리로 변환"""
        return {
            "idx": self.idx,
            "user_id": self.user_id,
            "plant_id": self.plant_id,
            "plant_name": self.plant_name,
            "species": self.species,
            "pest_id": self.pest_id,
            "meet_day": self.meet_day,
        }
