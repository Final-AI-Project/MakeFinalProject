from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional

from ..services import plants_service
from ..utils.security import get_current_user


class PlantCreateIn(BaseModel):
    nickname: str
    species_hint: Optional[str] = None
    planted_at: Optional[str] = None
    location: Optional[str] = None


class PlantPatchIn(BaseModel):
    nickname: Optional[str] = None
    location: Optional[str] = None


router = APIRouter(prefix="/plants", tags=["plants"])


@router.post("")
async def create_plant(data: PlantCreateIn, user=Depends(get_current_user)):
    return plants_service.create(user["id"], data)


@router.get("")
async def list_plants(
    limit: int = Query(10, gt=0),
    cursor: Optional[str] = None,
    user=Depends(get_current_user),
):
    return plants_service.list(user["id"], limit, cursor)


@router.get("/{plant_id}")
async def get_plant(plant_id: str, user=Depends(get_current_user)):
    return plants_service.get(user["id"], plant_id)


@router.patch("/{plant_id}")
async def patch_plant(plant_id: str, data: PlantPatchIn, user=Depends(get_current_user)):
    return plants_service.patch(user["id"], plant_id, data)
