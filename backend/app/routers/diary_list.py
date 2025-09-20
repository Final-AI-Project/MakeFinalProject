from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from schemas.diary import (
    DiaryListResponse,
    DiarySearchRequest,
    DiaryStatsResponse,
    DiaryListItemResponse
)
from repositories.diary_list import (
    get_user_diary_list,
    search_user_diaries,
    get_diary_stats,
    get_plant_diary_summary,
    get_recent_diaries
)
from services.auth_service import get_current_user

router = APIRouter(prefix="/diary-list", tags=["diary-list"])

@router.get("", response_model=DiaryListResponse)
async def get_diary_list(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    order_by: str = Query("created_at", description="정렬 기준 (created_at, updated_at, plant_nickname, plant_species, user_title)"),
    order_direction: str = Query("desc", description="정렬 방향 (asc, desc)"),
    plant_nickname: Optional[str] = Query(None, description="식물 별명으로 필터링"),
    plant_species: Optional[str] = Query(None, description="식물 종류로 필터링"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    hashtag: Optional[str] = Query(None, description="해시태그로 필터링"),
    user: dict = Depends(get_current_user)
):
    """
    사용자의 일기 목록을 조회합니다.
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **order_by**: 정렬 기준 (created_at, updated_at, plant_nickname, plant_species, user_title)
    - **order_direction**: 정렬 방향 (asc, desc)
    - **plant_nickname**: 식물 별명으로 필터링
    - **plant_species**: 식물 종류로 필터링
    - **start_date**: 시작 날짜 (YYYY-MM-DD 형식)
    - **end_date**: 종료 날짜 (YYYY-MM-DD 형식)
    - **hashtag**: 해시태그로 필터링
    """
    try:
        # 날짜 파싱
        start_date_parsed = None
        end_date_parsed = None
        
        if start_date:
            try:
                from datetime import datetime
                start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="시작 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용하세요.")
        
        if end_date:
            try:
                from datetime import datetime
                end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="종료 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용하세요.")
        
        # 일기 목록 조회
        diaries = await get_user_diary_list(
            user_id=user["user_id"],
            page=page,
            limit=limit,
            order_by=order_by,
            order_direction=order_direction,
            plant_nickname=plant_nickname,
            plant_species=plant_species,
            start_date=start_date_parsed,
            end_date=end_date_parsed,
            hashtag=hashtag
        )
        
        return diaries
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/search", response_model=DiaryListResponse)
async def search_diaries(
    request: DiarySearchRequest,
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    user: dict = Depends(get_current_user)
):
    """
    일기를 검색합니다.
    """
    try:
        diaries = await search_user_diaries(
            user_id=user["user_id"],
            request=request,
            page=page,
            limit=limit
        )
        
        return diaries
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 검색 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/stats", response_model=DiaryStatsResponse)
async def get_diary_statistics(
    user: dict = Depends(get_current_user)
):
    """
    사용자의 일기 통계를 조회합니다.
    """
    try:
        stats = await get_diary_stats(user["user_id"])
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/recent")
async def get_recent_diary_list(
    limit: int = Query(5, ge=1, le=20, description="조회할 최근 일기 수"),
    user: dict = Depends(get_current_user)
):
    """
    최근 작성된 일기 목록을 조회합니다.
    """
    try:
        recent_diaries = await get_recent_diaries(user["user_id"], limit)
        return {
            "diaries": recent_diaries,
            "total_count": len(recent_diaries)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"최근 일기 조회 중 오류가 발생했습니다: {str(e)}"
        )