from __future__ import annotations
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PlantWiki:
    """aiomysql용 PlantWiki 모델"""
    idx: Optional[int] = None
    species: str = ""
    wiki_image: Optional[str] = None
    sunlight: Optional[str] = None
    watering: Optional[str] = None
    flowering: Optional[str] = None
    fertilizer: Optional[str] = None
    toxicity: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlantWiki":
        """딕셔너리에서 PlantWiki 객체 생성"""
        return cls(
            idx=data.get("idx"),
            species=data.get("species", ""),
            wiki_image=data.get("wiki_image"),
            sunlight=data.get("sunlight"),
            watering=data.get("watering"),
            flowering=data.get("flowering"),
            fertilizer=data.get("fertilizer"),
            toxicity=data.get("toxicity"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """PlantWiki 객체를 딕셔너리로 변환"""
        return {
            "idx": self.idx,
            "species": self.species,
            "wiki_image": self.wiki_image,
            "sunlight": self.sunlight,
            "watering": self.watering,
            "flowering": self.flowering,
            "fertilizer": self.fertilizer,
            "toxicity": self.toxicity,
        }
