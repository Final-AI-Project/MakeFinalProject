from __future__ import annotations

import aiomysql
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from core.database import get_db
from crud import plant_wiki as plant_wiki_crud
from schemas.plant_wiki import (
    PlantWikiCreate, 
    PlantWikiOut,
    PlantWikiUpdate,
    PlantWikiListOut
)
from models.plant_wiki import PlantWiki

from utils.errors import http_error
from utils.security import get_current_user
from utils.pagination import (
    decode_id_cursor, 
    encode_id_cursor, 
    page_window
)

router = APIRouter(prefix="/plant-info", tags=["plant-info"])

def _to_out(row: PlantWiki) -> PlantWikiOut:
    """PlantWiki 모델을 PlantWikiOut 스키마로 변환"""
    return PlantWikiOut(
        idx=row.idx,
        species=row.species,
        wiki_image=row.wiki_image,
        sunlight=row.sunlight,
        watering=row.watering,
        flowering=row.flowering,
        fertilizer=row.fertilizer,
        toxicity=row.toxicity,
    )


@router.get("/tips", response_model=List[PlantWikiOut])
async def get_plant_tips(
    limit: int = Query(10, ge=1, le=50),
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    식물 TIP 목록 조회
    - 인기 있는 식물들의 관리 팁 제공
    """
    # 인기 있는 식물들의 기본 정보를 조회 (실제로는 조회수나 인기도 기준으로 정렬)
    rows = await plant_wiki_crud.list_by_cursor(
        db, limit=limit, last_idx=None
    )
    return [_to_out(row) for row in rows]


@router.get("/species", response_model=PlantWikiListOut)
async def get_plant_species(
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="식물 종류 검색"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    품종 관련 정보 조회
    - 식물 종류별 상세 정보 제공
    - 검색 기능 포함
    """
    last_idx = decode_id_cursor(cursor)
    
    if search:
        # 검색어가 있는 경우 species 필드에서 검색
        rows = await plant_wiki_crud.search_by_species(
            db, search_term=search, limit=limit, last_idx=last_idx
        )
    else:
        # 일반 목록 조회
        rows = await plant_wiki_crud.list_by_cursor(
            db, limit=limit, last_idx=last_idx
        )
    
    items, has_more = page_window(list(rows), limit)
    next_cursor = encode_id_cursor(items[-1].idx) if has_more else None
    
    return PlantWikiListOut(
        items=[_to_out(r) for r in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/growth", response_model=List[PlantWikiOut])
async def get_growth_info(
    category: Optional[str] = Query(None, description="카테고리: sunlight, watering, flowering, fertilizer"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    생육 관련 정보 조회
    - 햇빛, 물주기, 개화, 비료 등 카테고리별 정보 제공
    """
    if category and category in ['sunlight', 'watering', 'flowering', 'fertilizer']:
        # 특정 카테고리 정보만 조회
        rows = await plant_wiki_crud.get_by_category(
            db, category=category, limit=20
        )
    else:
        # 전체 생육 정보 조회
        rows = await plant_wiki_crud.list_by_cursor(
            db, limit=20, last_idx=None
        )
    
    return [_to_out(row) for row in rows]


@router.get("/{idx}", response_model=PlantWikiOut)
async def get_plant_info(
    idx: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    식물 정보 단건 조회
    - 특정 식물의 상세 정보 제공
    """
    row = await plant_wiki_crud.get_by_idx(db, idx)
    if not row:
        raise http_error("plant_info_not_found", "식물 정보를 찾을 수 없습니다.", 404)
    return _to_out(row)


@router.get("/species/{species}", response_model=PlantWikiOut)
async def get_plant_by_species(
    species: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    식물 종류로 정보 조회
    - species 이름으로 식물 정보 검색
    """
    row = await plant_wiki_crud.get_by_species(db, species)
    if not row:
        raise http_error("plant_species_not_found", f"'{species}' 종류의 식물 정보를 찾을 수 없습니다.", 404)
    return _to_out(row)


@router.post("", response_model=PlantWikiOut, status_code=status.HTTP_201_CREATED)
async def create_plant_info(
    body: PlantWikiCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    새 식물 정보 등록 (관리자용)
    """
    # 중복 species 체크
    existing = await plant_wiki_crud.get_by_species(db, body.species)
    if existing:
        raise http_error("species_already_exists", f"'{body.species}' 종류는 이미 등록되어 있습니다.", 400)
    
    row = await plant_wiki_crud.create(
        db,
        species=body.species,
        wiki_image=body.wiki_image,
        sunlight=body.sunlight,
        watering=body.watering,
        flowering=body.flowering,
        fertilizer=body.fertilizer,
        toxicity=body.toxicity,
    )
    return _to_out(row)


@router.patch("/{idx}", response_model=PlantWikiOut)
async def update_plant_info(
    idx: int,
    body: PlantWikiUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    식물 정보 수정 (관리자용)
    """
    row = await plant_wiki_crud.get_by_idx(db, idx)
    if not row:
        raise http_error("plant_info_not_found", "식물 정보를 찾을 수 없습니다.", 404)

    fields = body.model_dump(exclude_unset=True)
    if not any(v is not None for v in fields.values()):
        return _to_out(row)

    # species 변경 시 중복 체크
    if 'species' in fields and fields['species'] != row.species:
        existing = await plant_wiki_crud.get_by_species(db, fields['species'])
        if existing:
            raise http_error("species_already_exists", f"'{fields['species']}' 종류는 이미 등록되어 있습니다.", 400)

    updated = await plant_wiki_crud.patch(db, idx, **fields)
    return _to_out(updated or row)
