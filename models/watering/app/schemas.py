# app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class SensorPoint(BaseModel):
    ts: int = Field(..., description="epoch ms")
    soil_moist_pct: float = Field(..., ge=0, le=100)
    soil_temp_c: Optional[float] = None
    room_temp_c: Optional[float] = None
    room_rh_pct: Optional[float] = None

class WeatherPoint(BaseModel):
    ts: int
    outdoor_temp_c: float
    outdoor_rh_pct: float  # KMA
    irradiance_wpm2: Optional[float] = None  # 없으면 None

class PotMeta(BaseModel):
    plant_type: str = "generic"
    pot_diameter_cm: float = 14.0
    pot_height_cm: float = 12.0
    media_type: str = "peat_coco_perlite"
    theta_min_pct: float = 18.0  # 위험 임계치

class PredictRequest(BaseModel):
    history: List[SensorPoint]
    forecast: List[WeatherPoint]
    meta: PotMeta

class PredictResponse(BaseModel):
    eta_hours_p50: float
    eta_hours_p90: float
    path: List[float]  # 예측된 향후 수분% 시퀀스
