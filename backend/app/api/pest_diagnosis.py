from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime

from schemas.disease_diagnosis import (
    DiseaseDiagnosisResponse, UserPlantsResponse, UserPlantOption,
    DiseaseDiagnosisSaveRequest, DiseaseDiagnosisSaveResponse
)
from repositories.pest_diagnosis import (
    get_user_pest_diagnosis_history, get_pest_diagnosis_by_plant,
    get_pest_wiki_by_id, get_all_pest_wiki, save_pest_diagnosis_result,
    get_user_plants_with_pest_history, get_recent_pest_diagnoses,
    get_pest_diagnosis_statistics
)
from services.auth_service import get_current_user

router = APIRouter(prefix="/pest-diagnosis", tags=["pest-diagnosis"])


@router.get("/history")
async def get_pest_diagnosis_history(
    limit: int = Query(20, ge=1, le=100, description="조회할 진단 기록 수"),
    offset: int = Query(0, ge=0, description="건너뛸 진단 기록 수"),
    user: dict = Depends(get_current_user)
):
    """
    사용자의 병충해 진단 기록 목록 조회
    
    - **limit**: 조회할 진단 기록 수 (기본값: 20, 최대: 100)
    - **offset**: 건너뛸 진단 기록 수 (기본값: 0)
    """
    try:
        diagnoses = await get_user_pest_diagnosis_history(user["user_id"], limit, offset)
        return {
            "diagnoses": diagnoses,
            "total_count": len(diagnoses),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/plants/{plant_id}")
async def get_plant_pest_diagnosis_history(
    plant_id: int,
    user: dict = Depends(get_current_user)
):
    """
    특정 식물의 병충해 진단 기록 조회
    
    - **plant_id**: 식물 ID
    """
    try:
        diagnoses = await get_pest_diagnosis_by_plant(user["user_id"], plant_id)
        return {
            "plant_id": plant_id,
            "diagnoses": diagnoses,
            "total_count": len(diagnoses)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물별 병충해 진단 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/plants")
async def get_plants_with_pest_history(
    user: dict = Depends(get_current_user)
):
    """
    병충해 진단 기록이 있는 사용자 식물 목록 조회
    """
    try:
        plants = await get_user_plants_with_pest_history(user["user_id"])
        return {
            "plants": plants,
            "total_count": len(plants)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 기록이 있는 식물 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/recent")
async def get_recent_pest_diagnoses(
    limit: int = Query(10, ge=1, le=50, description="조회할 최근 진단 기록 수"),
    user: dict = Depends(get_current_user)
):
    """
    최근 병충해 진단 기록 조회
    
    - **limit**: 조회할 최근 진단 기록 수 (기본값: 10, 최대: 50)
    """
    try:
        diagnoses = await get_recent_pest_diagnoses(user["user_id"], limit)
        return {
            "diagnoses": diagnoses,
            "total_count": len(diagnoses)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"최근 병충해 진단 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/wiki/{pest_id}")
async def get_pest_wiki_info(
    pest_id: int,
    user: dict = Depends(get_current_user)
):
    """
    특정 병충해의 위키 정보 조회
    
    - **pest_id**: 병충해 ID
    """
    try:
        pest_info = await get_pest_wiki_by_id(pest_id)
        if not pest_info:
            raise HTTPException(status_code=404, detail="병충해 정보를 찾을 수 없습니다.")
        
        return pest_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 위키 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/wiki")
async def get_all_pest_wiki_info(
    user: dict = Depends(get_current_user)
):
    """
    모든 병충해 위키 정보 조회
    """
    try:
        pest_wiki_list = await get_all_pest_wiki()
        return {
            "pest_wiki": pest_wiki_list,
            "total_count": len(pest_wiki_list)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 위키 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/statistics")
async def get_pest_diagnosis_statistics_endpoint(
    user: dict = Depends(get_current_user)
):
    """
    병충해 진단 통계 조회
    """
    try:
        stats = await get_pest_diagnosis_statistics(user["user_id"])
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/save")
async def save_pest_diagnosis_result_endpoint(
    request: DiseaseDiagnosisSaveRequest,
    user: dict = Depends(get_current_user)
):
    """
    병충해 진단 결과 저장
    
    - **plant_id**: 식물 ID
    - **predictions**: 진단 결과 목록
    - **image_url**: 진단에 사용된 이미지 URL
    - **notes**: 추가 메모
    """
    try:
        diagnosis_id = await save_pest_diagnosis_result(
            user_id=user["user_id"],
            plant_id=request.plant_id,
            predictions=request.predictions,
            image_url=request.image_url,
            notes=request.notes
        )
        
        return DiseaseDiagnosisSaveResponse(
            success=True,
            message="병충해 진단 결과가 성공적으로 저장되었습니다.",
            diagnosis_id=diagnosis_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 결과 저장 중 오류가 발생했습니다: {str(e)}"
        )
