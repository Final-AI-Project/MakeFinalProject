from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class HumidInfo:
    """aiomysql용 HumidInfo 모델"""
    idx: Optional[int] = None
    plant_id: int = 0
    humidity: float = 0.0
    humid_date: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumidInfo":
        """딕셔너리에서 HumidInfo 객체 생성"""
        return cls(
            idx=data.get("idx"),
            plant_id=data.get("plant_id", 0),
            humidity=data.get("humidity", 0.0),
            humid_date=data.get("humid_date"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """HumidInfo 객체를 딕셔너리로 변환"""
        return {
            "idx": self.idx,
            "plant_id": self.plant_id,
            "humidity": self.humidity,
            "humid_date": self.humid_date,
        }
