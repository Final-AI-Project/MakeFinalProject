from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from utils.security import get_current_user
from services.dashboard_service import DashboardService

# ===메인화면 (dashboard) 라우터===
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# --- Schemas ---
# 날씨 정보 스키마
class WeatherBridgeIn(BaseModel):
    location_code: str = Field(..., examples=["SEOUL_KR"])
    name: str = Field(..., examples=["Seoul, KR"])
    temp_c: float
    condition: str = ""
    icon_url: str = ""
    updated_at: datetime | None = None

class WeatherBridgeOut(WeatherBridgeIn):
    server_received_at: datetime

# 식물 정보 카드 스키마
class PlantCardItem(BaseModel):
    plant_id: int
    plant_name: str
    species: Optional[str] = None
    pest_status: str = Field(..., examples=["healthy", "has_pest"])
    pest_id: Optional[int] = None
    humidity: Optional[float] = None
    humid_date: Optional[datetime] = None
    detail_path: str

# 커서 기반
class PlantCardsOut(BaseModel):
    items: List[PlantCardItem]
    next_cursor: Optional[str] = None
    has_more: bool = False


# --- 엔드포인트 ---
@router.post("/weather-bridge", response_model=WeatherBridgeOut)
async def weather_bridge(
    payload: WeatherBridgeIn,
    user: Dict[str,Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    프론트에서 넘긴 현재 날씨 정보를 서버 표준 포맷으로 정규화하여 반환합니다.
    - 저장은 하지 않습니다.
    """
    svc = DashboardService(db=db)
    out = await svc.normalize_weather_from_front(payload.model_dump())
    return WeatherBridgeOut(**out)



@router.get("/plants", response_model=PlantCardsOut)
async def get_my_plants_cards(
    limit: int = Query(5, ge=1, le=50),
    cursor: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    메인 화면 스와이프용 '내 식물' 리스트 (DB 연동)
    - user_plant 기준, 각 plant의 최신 humid_info 1건 포함
    """
    svc = DashboardService(db=db)
    data = await svc.list_plants_summary(user_id=user["user_id"], limit=limit, cursor=cursor)
    return PlantCardsOut(**data)