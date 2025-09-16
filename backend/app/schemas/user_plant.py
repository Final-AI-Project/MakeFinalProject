from __future__ import annotations
from datetime import datetime
from pydantic import Field
from typing import List, Optional
from .common import OrmBase
from .humid_info import HumidInfoOut 

class UserPlantCreate(OrmBase):
    plant_name: str = Field(min_length=1, max_length=100)
    species: str | None = Field(default=None, max_length=100)
    pest_id: int | None = None
    meet_day: datetime | None = None

class UserPlantUpdate(OrmBase):
    plant_name: str | None = None
    species: str | None = None
    pest_id: int | None = None
    meet_day: datetime | None = None

# 식물 정보 response
class UserPlantOut(OrmBase):
    idx: int
    user_id: str
    plant_id: int
    plant_name: str
    species: str | None
    pest_id: int | None
    meet_day: datetime | None

    # 관계 포함(선택): 최근 N개만 보여주고 싶다면 서비스에서 슬라이싱
    humid_infos: list["HumidInfoOut"] = []

# 대시보드 리스트화
class PlantListOut(OrmBase):
    items: List[UserPlantOut]
    next_cursor: Optional[str] = None
    has_more: bool = False
