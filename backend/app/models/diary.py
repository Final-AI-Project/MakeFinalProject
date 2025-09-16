from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Diary:
    """aiomysql용 Diary 모델"""
    idx: Optional[int] = None
    user_id: str = ""
    user_title: str = ""
    img_url: Optional[str] = None
    user_content: str = ""
    hashtag: Optional[str] = None
    plant_content: Optional[str] = None
    weather: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Diary":
        """딕셔너리에서 Diary 객체 생성"""
        return cls(
            idx=data.get("idx"),
            user_id=data.get("user_id", ""),
            user_title=data.get("user_title", ""),
            img_url=data.get("img_url"),
            user_content=data.get("user_content", ""),
            hashtag=data.get("hashtag"),
            plant_content=data.get("plant_content"),
            weather=data.get("weather"),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Diary 객체를 딕셔너리로 변환"""
        return {
            "idx": self.idx,
            "user_id": self.user_id,
            "user_title": self.user_title,
            "img_url": self.img_url,
            "user_content": self.user_content,
            "hashtag": self.hashtag,
            "plant_content": self.plant_content,
            "weather": self.weather,
            "created_at": self.created_at,
        }
