from __future__ import annotations
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ImgAddress:
    """aiomysql용 ImgAddress 모델"""
    idx: Optional[int] = None
    diary_id: int = 0
    img_url: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImgAddress":
        """딕셔너리에서 ImgAddress 객체 생성"""
        return cls(
            idx=data.get("idx"),
            diary_id=data.get("diary_id", 0),
            img_url=data.get("img_url", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """ImgAddress 객체를 딕셔너리로 변환"""
        return {
            "idx": self.idx,
            "diary_id": self.diary_id,
            "img_url": self.img_url,
        }
