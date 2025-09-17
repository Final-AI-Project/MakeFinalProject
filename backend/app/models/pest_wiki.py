from __future__ import annotations
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PestWiki:
    """aiomysql용 PestWiki 모델"""
    idx: Optional[int] = None
    pest_id: int = 0
    cause: Optional[str] = None
    cure: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PestWiki":
        """딕셔너리에서 PestWiki 객체 생성"""
        return cls(
            idx=data.get("idx"),
            pest_id=data.get("pest_id", 0),
            cause=data.get("cause"),
            cure=data.get("cure"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """PestWiki 객체를 딕셔너리로 변환"""
        return {
            "idx": self.idx,
            "pest_id": self.pest_id,
            "cause": self.cause,
            "cure": self.cure,
        }
