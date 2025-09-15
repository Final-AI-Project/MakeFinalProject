from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..db.crud import user_plant as user_plant_crud
from ..db.schemas.user_plant import (
    UserPlantCreate, 
    UserPlantOut,
    UserPlantUpdate,
    PlantListOut
    )
from ..db.models.user_plant import UserPlant

from ..utils.errors import http_error
from ..utils.security import get_current_user
from ..utils.pagination import (
    decode_id_cursor, 
    encode_id_cursor, 
    page_window
    )

router = APIRouter(prefix="/plants", tags=["plants"])

def _to_out(row: UserPlant) -> UserPlantOut:
    # humid_infos는 일단 기본값, 필요 시 서비스에서 채워 넣습니다
    return UserPlantOut(
        idx=row.idx,
        user_id=row.user_id,
        plant_id=row.plant_id,
        plant_name=row.plant_name,
        species=row.species,
        pest_id=row.pest_id,
        meet_day=row.meet_day,        
    )



@router.post("", response_model=UserPlantOut, status_code=status.HTTP_201_CREATED)
async def create_plant(
    body: UserPlantCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """"""
    # plant_id 중복 검증
    exists = await user_plant_crud.get_by_plant_id(db, body.plant_id)
    if exists:
        raise http_error("plant_conflict", "이미 등록된 plant_id 입니다.", 409)
    
    row = await user_plant_crud.create(
        db,
        user_id=user["user_id"],
        plant_id=body.plant_id,
        plant_name=body.plant_name,
        species=body.species,
        pest_id=body.pest_id,
        meet_day=body.meet_day,
    )
    return _to_out(row)


@router.get("", response_model=PlantListOut)
async def list_plants(
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    내 식물 목록 (커서 기반, idx DESC)
    - cursor: encode_id_cursor(last_idx) / decode_id_cursor
    """
    last_idx = decode_id_cursor(cursor)
    rows = await user_plant_crud.list_by_user_cursor(
        db, user_id=user["user_id"], limit=limit, last_idx=last_idx
    )
    items, has_more = page_window(list(rows), limit)
    next_cursor = encode_id_cursor(items[-1].idx) if has_more else None
    return PlantListOut(
        items=[_to_out(r) for r in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/{plant_id}", response_model=UserPlantOut)
async def get_plant(
    plant_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    식물 단건 조회 (plant_id 기준)
    - 소유자(user_id) 검증
    """
    row = await user_plant_crud.get_by_plant_id(db, plant_id)
    if not row or row.user_id != user["user_id"]:
        raise http_error("plant_not_found", "식물을 찾을 수 없습니다.", 404)
    return _to_out(row)


@router.patch("/{plant_id}", response_model=UserPlantOut)
async def patch_plant(
    plant_id: int,
    body: UserPlantUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    식물 수정 (plant_id 기준)
    - 내부적으로 idx를 찾아 patch
    - 업데이트 필드가 없으면 기존값 반환
    """
    row = await user_plant_crud.get_by_plant_id(db, plant_id)
    if not row or row.user_id != user["user_id"]:
        raise http_error("plant_not_found", "식물을 찾을 수 없습니다.", 404)

    fields = body.model_dump(exclude_unset=True)
    if not any(v is not None for v in fields.values()):
        return _to_out(row)

    updated = await user_plant_crud.patch(db, row.idx, **fields)
    return _to_out(updated or row)