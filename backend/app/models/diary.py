from __future__ import annotations
from datetime import datetime, date
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Diary:
    """aiomysql용 Diary 모델 - Final.sql 구조에 맞춤"""
    diary_id: Optional[int] = None
    user_id: str = ""
    user_title: str = ""
    user_content: str = ""
    hashtag: Optional[str] = None
    plant_id: Optional[int] = None
    plant_content: Optional[str] = None
    weather: Optional[str] = None
    hist_watered: Optional[int] = None
    hist_repot: Optional[int] = None
    hist_pruning: Optional[int] = None
    hist_fertilize: Optional[int] = None
    created_at: Optional[date] = None
    img_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Diary":
        """딕셔너리에서 Diary 객체 생성"""
        return cls(
            diary_id=data.get("diary_id"),
            user_id=data.get("user_id", ""),
            user_title=data.get("user_title", ""),
            user_content=data.get("user_content", ""),
            hashtag=data.get("hashtag"),
            plant_id=data.get("plant_id"),
            plant_content=data.get("plant_content"),
            weather=data.get("weather"),
            hist_watered=data.get("hist_watered"),
            hist_repot=data.get("hist_repot"),
            hist_pruning=data.get("hist_pruning"),
            hist_fertilize=data.get("hist_fertilize"),
            created_at=data.get("created_at"),
            img_url=data.get("img_url"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Diary 객체를 딕셔너리로 변환"""
        return {
            "diary_id": self.diary_id,
            "user_id": self.user_id,
            "user_title": self.user_title,
            "user_content": self.user_content,
            "hashtag": self.hashtag,
            "plant_id": self.plant_id,
            "plant_content": self.plant_content,
            "weather": self.weather,
            "hist_watered": self.hist_watered,
            "hist_repot": self.hist_repot,
            "hist_pruning": self.hist_pruning,
            "hist_fertilize": self.hist_fertilize,
            "created_at": self.created_at,
            "img_url": self.img_url,
        }
