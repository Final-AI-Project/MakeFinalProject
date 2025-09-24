from fastapi import APIRouter, HTTPException, Depends
from typing import List
from schemas.plant_detail import (
    PlantDetailResponse, 
    PlantUpdateRequest, 
    PlantDeleteRequest,
    PlantDetailSummaryResponse,
    PlantSpeciesInfoResponse
)
from repositories.plant_detail import (
    get_plant_detail, 
    update_plant_info, 
    delete_plant,
    get_plant_detail_summary,
    get_plant_species_info
)
from services.auth_service import get_current_user

router = APIRouter(prefix="/plant-detail", tags=["plant-detail"])

@router.get("/{plant_idx}", response_model=PlantDetailResponse)
async def get_plant_detail_info(
    plant_idx: int, 
    user: dict = Depends(get_current_user)
):
    """
    특정 식물의 상세 정보를 조회합니다.
    별명, 품종, 키우기 시작한날, 건강상태, 습도, 품종 정보 등을 포함합니다.
    """
    try:
        result = await get_plant_detail(plant_idx, user['user_id'])
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 상세 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/summary", response_model=PlantDetailSummaryResponse)
async def get_plant_detail_summary_info(plant_idx: int, user_id: str):
    """
    식물의 상세 요약 정보를 조회합니다.
    기본 정보, 최근 일기, 병해충 기록, 습도 트렌드, 관리 알림을 포함합니다.
    """
    try:
        result = await get_plant_detail_summary(plant_idx, user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 요약 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/{plant_idx}")
async def update_plant_detail_info(plant_idx: int, user_id: str, update_data: PlantUpdateRequest):
    """
    식물 정보를 수정합니다.
    별명, 품종, 키우기 시작한날, 키우는 장소 등을 수정할 수 있습니다.
    """
    try:
        # Pydantic 모델을 dict로 변환하고 None 값 제거
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="수정할 정보가 없습니다.")
        
        success = await update_plant_info(plant_idx, user_id, update_dict)
        
        if success:
            return {
                "message": "식물 정보가 성공적으로 수정되었습니다.",
                "plant_idx": plant_idx,
                "updated_fields": list(update_dict.keys())
            }
        else:
            raise HTTPException(status_code=404, detail="식물을 찾을 수 없거나 수정 권한이 없습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 정보 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/{plant_idx}")
async def delete_plant_detail(plant_idx: int, user_id: str, delete_request: PlantDeleteRequest):
    """
    식물을 삭제합니다.
    죽거나 버리거나 다른 곳에 심거나 하는 경우에 사용합니다.
    """
    try:
        # 요청의 user_id와 plant_idx가 일치하는지 확인
        if delete_request.user_id != user_id or delete_request.plant_idx != plant_idx:
            raise HTTPException(status_code=400, detail="요청 정보가 일치하지 않습니다.")
        
        success = await delete_plant(plant_idx, user_id)
        
        if success:
            return {
                "message": "식물이 성공적으로 삭제되었습니다.",
                "plant_idx": plant_idx,
                "reason": delete_request.reason or "사용자 요청"
            }
        else:
            raise HTTPException(status_code=404, detail="식물을 찾을 수 없거나 삭제 권한이 없습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/health-check")
async def plant_detail_health_check(plant_idx: int, user_id: str):
    """
    식물 상세 정보 API 상태 확인
    """
    return {
        "status": "healthy",
        "message": "Plant Detail API is running",
        "plant_idx": plant_idx,
        "user_id": user_id,
        "version": "1.0.0"
    }

@router.get("/{plant_idx}/species-info", response_model=PlantSpeciesInfoResponse)
async def get_plant_species_info_endpoint(plant_idx: int, user_id: str):
    """
    식물의 품종 정보를 plant_wiki에서 조회합니다.
    DB 연동으로 해당 품종의 상세 정보를 제공합니다.
    """
    try:
        species_info = await get_plant_species_info(plant_idx, user_id)
        return species_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"품종 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )
