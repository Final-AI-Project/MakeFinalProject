from __future__ import annotations

import aiomysql
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from core.database import get_db
from crud import diary as diary_crud
from schemas.diary import (
    DiaryCreate, 
    DiaryOut,
    DiaryUpdate,
    DiaryListOut
)
from models.diary import Diary

from utils.errors import http_error
from utils.security import get_current_user
from utils.pagination import (
    decode_id_cursor, 
    encode_id_cursor, 
    page_window
)

router = APIRouter(prefix="/diary-list", tags=["diary-list"])

class SortOrder(str, Enum):
    """정렬 순서"""
    ASC = "asc"      # 오름차순 (오래된 것부터)
    DESC = "desc"    # 내림차순 (최신 것부터)

class SortBy(str, Enum):
    """정렬 기준"""
    DATE = "date"           # 날짜별
    TITLE = "title"         # 제목별
    CREATED_AT = "created_at"  # 생성일별

def _to_out(row: Diary) -> DiaryOut:
    """Diary 모델을 DiaryOut 스키마로 변환"""
    return DiaryOut(
        idx=row.idx,
        user_id=row.user_id,
        user_title=row.user_title,
        img_url=row.img_url,
        user_content=row.user_content,
        hashtag=row.hashtag,
        plant_content=row.plant_content,
        weather=row.weather,
        created_at=row.created_at,
        images=[],  # 이미지는 별도 조회 필요시 추가
    )


@router.get("", response_model=DiaryListOut)
async def get_diary_list(
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    cursor: Optional[str] = Query(None, description="페이지네이션 커서"),
    sort_by: SortBy = Query(SortBy.CREATED_AT, description="정렬 기준"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="정렬 순서"),
    plant_filter: Optional[str] = Query(None, description="식물별 필터링 (plant_content에서 검색)"),
    date_from: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    내 식물 전부 일기 목록 조회
    - 날짜별, 식물별 정렬 및 필터링 지원
    - 커서 기반 페이지네이션
    """
    last_idx = decode_id_cursor(cursor)
    
    # 정렬 기준에 따른 ORDER BY 절 생성
    order_by_map = {
        SortBy.DATE: "created_at",
        SortBy.TITLE: "user_title", 
        SortBy.CREATED_AT: "created_at"
    }
    
    order_by_field = order_by_map[sort_by]
    order_direction = "ASC" if sort_order == SortOrder.ASC else "DESC"
    
    # 필터링 조건 생성
    where_conditions = ["user_id = %s"]
    params = [user["user_id"]]
    
    # 식물별 필터링
    if plant_filter:
        where_conditions.append("(plant_content LIKE %s OR user_title LIKE %s)")
        plant_search = f"%{plant_filter}%"
        params.extend([plant_search, plant_search])
    
    # 날짜 범위 필터링
    if date_from:
        where_conditions.append("DATE(created_at) >= %s")
        params.append(date_from)
    
    if date_to:
        where_conditions.append("DATE(created_at) <= %s")
        params.append(date_to)
    
    # 커서 기반 페이지네이션 조건
    if last_idx is not None:
        if sort_order == SortOrder.DESC:
            where_conditions.append("idx < %s")
        else:
            where_conditions.append("idx > %s")
        params.append(last_idx)
    
    # WHERE 절 조합
    where_clause = " AND ".join(where_conditions)
    
    # ORDER BY 절
    order_clause = f"ORDER BY {order_by_field} {order_direction}, idx {order_direction}"
    
    # LIMIT 절
    limit_clause = f"LIMIT {limit + 1}"
    
    # 최종 쿼리
    query = f"""
        SELECT * FROM diary 
        WHERE {where_clause}
        {order_clause}
        {limit_clause}
    """
    
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(query, params)
        results = await cursor.fetchall()
    
    diaries = [Diary.from_dict(row) for row in results]
    
    # 페이지네이션 처리
    items, has_more = page_window(diaries, limit)
    next_cursor = encode_id_cursor(items[-1].idx) if has_more else None
    
    return DiaryListOut(
        items=[_to_out(r) for r in items],
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=len(diaries),  # 현재 페이지 기준 개수
    )


@router.get("/stats", response_model=Dict[str, Any])
async def get_diary_stats(
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    일기 통계 정보 조회
    - 총 일기 수, 월별 작성 수, 식물별 일기 수 등
    """
    async with db.cursor(aiomysql.DictCursor) as cursor:
        # 총 일기 수
        await cursor.execute(
            "SELECT COUNT(*) as total_count FROM diary WHERE user_id = %s",
            (user["user_id"],)
        )
        total_result = await cursor.fetchone()
        total_count = total_result["total_count"] if total_result else 0
        
        # 이번 달 일기 수
        await cursor.execute(
            """
            SELECT COUNT(*) as monthly_count 
            FROM diary 
            WHERE user_id = %s 
            AND YEAR(created_at) = YEAR(NOW()) 
            AND MONTH(created_at) = MONTH(NOW())
            """,
            (user["user_id"],)
        )
        monthly_result = await cursor.fetchone()
        monthly_count = monthly_result["monthly_count"] if monthly_result else 0
        
        # 최근 일기 작성일
        await cursor.execute(
            """
            SELECT MAX(created_at) as last_diary_date 
            FROM diary 
            WHERE user_id = %s
            """,
            (user["user_id"],)
        )
        last_date_result = await cursor.fetchone()
        last_diary_date = last_date_result["last_diary_date"] if last_date_result else None
        
        # 식물별 일기 수 (상위 5개)
        await cursor.execute(
            """
            SELECT plant_content, COUNT(*) as count 
            FROM diary 
            WHERE user_id = %s AND plant_content IS NOT NULL AND plant_content != ''
            GROUP BY plant_content 
            ORDER BY count DESC 
            LIMIT 5
            """,
            (user["user_id"],)
        )
        plant_stats = await cursor.fetchall()
    
    return {
        "total_count": total_count,
        "monthly_count": monthly_count,
        "last_diary_date": last_diary_date,
        "top_plants": [
            {"plant": row["plant_content"], "count": row["count"]} 
            for row in plant_stats
        ]
    }


@router.get("/search", response_model=DiaryListOut)
async def search_diaries(
    q: str = Query(..., min_length=1, description="검색어"),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    일기 내용 검색
    - 제목, 내용, 해시태그에서 검색
    """
    last_idx = decode_id_cursor(cursor)
    
    search_pattern = f"%{q}%"
    where_conditions = [
        "user_id = %s",
        "(user_title LIKE %s OR user_content LIKE %s OR hashtag LIKE %s OR plant_content LIKE %s)"
    ]
    
    params = [user["user_id"], search_pattern, search_pattern, search_pattern, search_pattern]
    
    if last_idx is not None:
        where_conditions.append("idx < %s")
        params.append(last_idx)
    
    where_clause = " AND ".join(where_conditions)
    
    query = f"""
        SELECT * FROM diary 
        WHERE {where_clause}
        ORDER BY created_at DESC, idx DESC
        LIMIT {limit + 1}
    """
    
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(query, params)
        results = await cursor.fetchall()
    
    diaries = [Diary.from_dict(row) for row in results]
    items, has_more = page_window(diaries, limit)
    next_cursor = encode_id_cursor(items[-1].idx) if has_more else None
    
    return DiaryListOut(
        items=[_to_out(r) for r in items],
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=len(diaries),
    )
