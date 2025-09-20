from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from schemas.info_room import (
    PlantInfoResponse,
    PlantInfoListResponse,
    PlantInfoSearchRequest
)
from repositories.info_room import (
    get_plant_info_list,
    get_plant_info_by_id,
    search_plant_info,
    get_plant_info_by_species
)
from services.auth_service import get_current_user

router = APIRouter(prefix="/info-room", tags=["info-room"])

@router.get("", response_model=PlantInfoListResponse)
async def get_plant_info_list_endpoint(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    species: Optional[str] = Query(None, description="식물 종류로 필터링"),
    user: dict = Depends(get_current_user)
):
    """
    식물 정보 목록을 조회합니다.
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **species**: 식물 종류로 필터링
    """
    try:
        plant_info_list = await get_plant_info_list(
            page=page,
            limit=limit,
            species=species
        )
        
        return plant_info_list
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 정보 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_id}", response_model=PlantInfoResponse)
async def get_plant_info_detail(
    plant_id: int,
    user: dict = Depends(get_current_user)
):
    """
    특정 식물의 상세 정보를 조회합니다.
    
    - **plant_id**: 식물 ID
    """
    try:
        plant_info = await get_plant_info_by_id(plant_id)
        if not plant_info:
            raise HTTPException(status_code=404, detail="식물 정보를 찾을 수 없습니다.")
        
        return plant_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/species/{species}", response_model=PlantInfoResponse)
async def get_plant_info_by_species_endpoint(
    species: str,
    user: dict = Depends(get_current_user)
):
    """
    식물 종류로 식물 정보를 조회합니다.
    
    - **species**: 식물 종류
    """
    try:
        plant_info = await get_plant_info_by_species(species)
        if not plant_info:
            raise HTTPException(status_code=404, detail="해당 종류의 식물 정보를 찾을 수 없습니다.")
        
        return plant_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/search", response_model=PlantInfoListResponse)
async def search_plant_info_endpoint(
    request: PlantInfoSearchRequest,
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    user: dict = Depends(get_current_user)
):
    """
    식물 정보를 검색합니다.
    """
    try:
        search_results = await search_plant_info(
            request=request,
            page=page,
            limit=limit
        )
        
        return search_results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 정보 검색 중 오류가 발생했습니다: {str(e)}"
        )