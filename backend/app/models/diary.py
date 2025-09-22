from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Diary:
    """aiomysql용 Diary 모델"""
    diary_id: Optional[int] = None
    user_id: str = ""
    user_title: str = ""
    img_url: Optional[str] = None
    user_content: str = ""
    hashtag: Optional[str] = None
    plant_nickname: Optional[str] = None  # 식물별명
    plant_species: Optional[str] = None   # 식물종류
    plant_content: Optional[str] = None   # 식물의 답변
    weather: Optional[str] = None
    weather_icon: Optional[str] = None    # 날씨 아이콘 URL
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Diary":
        """딕셔너리에서 Diary 객체 생성"""
        return cls(
            diary_id=data.get("diary_id"),
            user_id=data.get("user_id", ""),
            user_title=data.get("user_title", ""),
            img_url=data.get("img_url"),
            user_content=data.get("user_content", ""),
            hashtag=data.get("hashtag"),
            plant_nickname=data.get("plant_nickname"),
            plant_species=data.get("plant_species"),
            plant_content=data.get("plant_content"),
            weather=data.get("weather"),
            weather_icon=data.get("weather_icon"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Diary 객체를 딕셔너리로 변환"""
        return {
            "diary_id": self.diary_id,
            "user_id": self.user_id,
            "user_title": self.user_title,
            "img_url": self.img_url,
            "user_content": self.user_content,
            "hashtag": self.hashtag,
            "plant_nickname": self.plant_nickname,
            "plant_species": self.plant_species,
            "plant_content": self.plant_content,
            "weather": self.weather,
            "weather_icon": self.weather_icon,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
