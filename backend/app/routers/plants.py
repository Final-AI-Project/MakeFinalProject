from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ..services import plants_service
from ..utils.security import get_current_user

router = APIRouter(prefix="/plants", tags=["plants"])


# ====== Schemas ======
class PlantCreateIn(BaseModel):
    nickname: str = Field(min_length=1)
    species_hint: Optional[str] = None
    planted_at: Optional[datetime] = None
    location: Optional[str] = None


class PlantPatchIn(BaseModel):
    nickname: Optional[str] = None
    location: Optional[str] = None


class PlantOut(BaseModel):
    id: str
    user_id: str
    nickname: str
    species_hint: Optional[str] = None
    planted_at: Optional[str] = None
    location: Optional[str] = None
    created_at: str
    updated_at: str


class PlantListOut(BaseModel):
    items: List[PlantOut]
    next_cursor: Optional[str] = None
    has_more: bool


# ====== Routes ======
@router.post("", response_model=PlantOut)
async def create_plant(body: PlantCreateIn, current_user=Depends(get_current_user)):
    plant = plants_service.create(current_user["id"], body.dict())
    return plant


# plant 리스트 조회 (페이지네이션 주석 처리로 인해 임시 주석 처리)

# @router.get("", response_model=PlantListOut)
# async def list_plants(
#     limit: int = Query(10, ge=1, le=100),
#     cursor: Optional[str] = Query(None),
#     current_user=Depends(get_current_user),
# ):
#     return plants_service.list(current_user["id"], limit=limit, cursor=cursor)

# plant 상세 조회
@router.get("/{plant_id}", response_model=PlantOut)
async def get_plant(plant_id: str, current_user=Depends(get_current_user)):
    return plants_service.get(current_user["id"], plant_id)

# plant 수정
@router.patch("/{plant_id}", response_model=PlantOut)
async def patch_plant(plant_id: str, body: PlantPatchIn, current_user=Depends(get_current_user)):
    return plants_service.patch(current_user["id"], plant_id, body.dict())
