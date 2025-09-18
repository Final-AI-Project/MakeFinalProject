from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from schemas.info_room import (
    PlantWikiListResponse,
    PestWikiListResponse,
    PlantWikiDetailResponse,
    PestWikiDetailResponse,
    InfoRoomStatsResponse
)
from crud.info_room import (
    get_plant_wiki_list,
    get_plant_wiki_detail,
    get_pest_wiki_list,
    get_pest_wiki_detail,
    get_info_room_stats,
    search_plant_wiki_by_category
)

router = APIRouter(prefix="/info-room", tags=["info-room"])

@router.get("/plants", response_model=PlantWikiListResponse)
async def get_plant_wiki_list_endpoint(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="식물명 검색")
):
    """
    식물 위키 목록을 조회합니다.
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **search**: 식물명으로 검색 (선택사항)
    """
    try:
        result = await get_plant_wiki_list(page=page, limit=limit, search=search)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 위키 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/plants/{wiki_plant_id}", response_model=PlantWikiDetailResponse)
async def get_plant_wiki_detail_endpoint(wiki_plant_id: int):
    """
    특정 식물의 위키 상세 정보를 조회합니다.
    
    - **wiki_plant_id**: 식물 위키 ID
    """
    try:
        result = await get_plant_wiki_detail(wiki_plant_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail="해당 식물 정보를 찾을 수 없습니다."
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 위키 상세 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/pests", response_model=PestWikiListResponse)
async def get_pest_wiki_list_endpoint(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="병충해명 검색")
):
    """
    병충해 위키 목록을 조회합니다.
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **search**: 병충해명으로 검색 (선택사항)
    """
    try:
        result = await get_pest_wiki_list(page=page, limit=limit, search=search)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 위키 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/pests/{pest_id}", response_model=PestWikiDetailResponse)
async def get_pest_wiki_detail_endpoint(pest_id: int):
    """
    특정 병충해의 위키 상세 정보를 조회합니다.
    
    - **pest_id**: 병충해 위키 ID
    """
    try:
        result = await get_pest_wiki_detail(pest_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail="해당 병충해 정보를 찾을 수 없습니다."
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 위키 상세 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/stats", response_model=InfoRoomStatsResponse)
async def get_info_room_stats_endpoint():
    """
    정보방 통계 정보를 조회합니다.
    
    - 전체 식물 수
    - 전체 병충해 수
    - 마지막 업데이트 시간
    """
    try:
        result = await get_info_room_stats()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"정보방 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/plants/category/{category}", response_model=PlantWikiListResponse)
async def get_plant_wiki_by_category_endpoint(
    category: str,
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수")
):
    """
    카테고리별 식물 위키를 조회합니다.
    
    - **category**: 카테고리 (flowering, indoor, outdoor, easy_care)
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    
    지원 카테고리:
    - flowering: 개화하는 식물
    - indoor: 실내 식물
    - outdoor: 야외 식물
    - easy_care: 관리하기 쉬운 식물
    """
    try:
        # 지원되는 카테고리 검증
        valid_categories = ["flowering", "indoor", "outdoor", "easy_care"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"지원되지 않는 카테고리입니다. 지원 카테고리: {', '.join(valid_categories)}"
            )
        
        result = await search_plant_wiki_by_category(
            category=category,
            page=page,
            limit=limit
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"카테고리별 식물 위키 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/search", response_model=PlantWikiListResponse)
async def search_plant_wiki_endpoint(
    q: str = Query(..., min_length=1, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수")
):
    """
    식물 위키를 통합 검색합니다.
    
    - **q**: 검색어 (필수)
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    """
    try:
        result = await get_plant_wiki_list(page=page, limit=limit, search=q)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 위키 검색 중 오류가 발생했습니다: {str(e)}"
        )
