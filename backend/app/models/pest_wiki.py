from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PestWiki:
    """aiomysql용 PestWiki 모델"""
    pest_id: Optional[int] = None
    pest_name: str = ""
    pathogen: Optional[str] = None
    symptom: Optional[str] = None
    cause: Optional[str] = None
    cure: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PestWiki":
        """딕셔너리에서 PestWiki 객체 생성"""
        return cls(
            pest_id=data.get("pest_id"),
            pest_name=data.get("pest_name", ""),
            pathogen=data.get("pathogen"),
            symptom=data.get("symptom"),
            cause=data.get("cause"),
            cure=data.get("cure"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """PestWiki 객체를 딕셔너리로 변환"""
        return {
            "pest_id": self.pest_id,
            "pest_name": self.pest_name,
            "pathogen": self.pathogen,
            "symptom": self.symptom,
            "cause": self.cause,
            "cure": self.cure,
        }
