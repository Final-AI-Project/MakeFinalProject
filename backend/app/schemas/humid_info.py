from __future__ import annotations
from datetime import datetime
from pydantic import Field
from .common import OrmBase

class HumidInfoCreate(OrmBase):
    plant_id: int
    humid_date: datetime
    humidity: float = Field(ge=0.0, le=100.0)

class HumidInfoOut(OrmBase):
    idx: int
    plant_id: int
    humidity: float
    humid_date: datetime
