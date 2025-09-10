from __future__ import annotations

import asyncio
import base64
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..services.dashboard_service import DashboardService
from ..services.users_service import (
    get_current_user,
    UsersService,
)
from ..utils.weather_client import WeatherClient

router = APIRouter()

# ======================
# Pydantic Schemas (v2)
# ======================

class WeatherOut(BaseModel):
    location_code: str
    name: str
    temp_c: float
    condition: str
    icon_url: str
    updated_at: datetime

class PlantSummaryItem(BaseModel):
    plant_id: str
    nickname: str
    brief_status: str
    last_update_at: datetime
    thumbnail_url: Optional[str] = None
    detail_path: str

class PlantsListOut(BaseModel):
    items: List[PlantSummaryItem]
    next_cursor: Optional[str] = None
    has_more: bool = False

class RoutesOut(BaseModel):
    main: str = "/"
    diary: str = "/diary"
    profile: str = "/profile"

class DashboardSummaryOut(BaseModel):
    weather: Optional[WeatherOut] = None
    plants: PlantsListOut
    routes: RoutesOut = RoutesOut()

# Preferences (users/me/preferences)
class WeatherLocation(BaseModel):
    location_code: str = Field(..., examples=["SEOUL_KR"])
    name: str = Field(..., examples=["Seoul, KR"])

class PreferencesOut(BaseModel):
    weather_location: WeatherLocation

class PreferencesPatchIn(BaseModel):
    weather_location: WeatherLocation

# ======================
# Helpers
# ======================

def _error_payload(code: str, message: str) -> Dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "trace_id": str(uuid.uuid4()),
        }
    }

# ======================
# Endpoints
# ======================

@router.get("/dashboard/summary", response_model=DashboardSummaryOut)
async def get_dashboard_summary(
    limit_plants: int = Query(5, ge=1, le=50),
    cursor_plants: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    통합 대시보드 요약:
      - 선호 지역 기반 날씨
      - 식물 요약 리스트(커서 기반 페이지네이션)
      - 정적 라우트 정보
    """
    user_id = user["user_id"]

    users_svc = UsersService()
    weather_client = WeatherClient()
    dash_svc = DashboardService(weather_client=weather_client, users_service=users_svc)

    try:
        # users/me/preferences, weather, plants 를 병렬 수집
        prefs_task = asyncio.create_task(users_svc.get_preferences(user_id))
        plants_task = asyncio.create_task(
            dash_svc.list_plants_summary(user_id=user_id, limit=limit_plants, cursor=cursor_plants)
        )
        # prefs 먼저 필요 → 위치 코드 추출 후 날씨 호출
        prefs = await prefs_task
        weather_task = asyncio.create_task(
            dash_svc.get_weather_for_preference(prefs=prefs)
        )

        plants_out, weather_out = await asyncio.gather(plants_task, weather_task)

        weather_model = WeatherOut(**weather_out) if weather_out else None
        plants_model = PlantsListOut(**plants_out)

    
    except Exception as e:
        # 안전한 에러 포맷
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload("INTERNAL_ERROR", f"failed to build dashboard: {e}"),
        )

    return DashboardSummaryOut(weather=weather_model, plants=plants_model, routes=RoutesOut())


@router.get("/dashboard/plants", response_model=PlantsListOut)
async def get_dashboard_plants_only(
    limit: int = Query(5, ge=1, le=50),
    cursor: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """식물 요약 리스트 전용 (프론트 최적화용)"""
    dash_svc = DashboardService(weather_client=WeatherClient(), users_service=UsersService())
    return await dash_svc.list_plants_summary(user_id=user["user_id"], limit=limit, cursor=cursor)


@router.get("/users/me/preferences", response_model=PreferencesOut)
async def get_me_preferences(
    user: Dict[str, Any] = Depends(get_current_user),
):
    """사용자 선호 지역 조회 (없으면 합리적 기본값으로 초기화)"""
    prefs = await UsersService().get_preferences(user["user_id"])
    return PreferencesOut(weather_location=WeatherLocation(**prefs["weather_location"]))


@router.patch("/users/me/preferences", response_model=PreferencesOut)
async def patch_me_preferences(
    payload: PreferencesPatchIn,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """사용자 선호 지역 저장/수정"""
    try:
        updated = await UsersService().update_preferences(
            user_id=user["user_id"], weather_location=payload.weather_location.model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_payload("BAD_REQUEST", f"invalid preferences: {e}"),
        )
    return PreferencesOut(weather_location=WeatherLocation(**updated["weather_location"]))
