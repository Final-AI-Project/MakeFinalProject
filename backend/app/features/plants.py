from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import date
import aiomysql

from schemas.plant_registration import (
    PlantRegistrationRequest,
    PlantRegistrationResponse,
    PlantListResponse,
    PlantUpdateRequest,
    PlantUpdateResponse,
    SpeciesClassificationRequest,
    SpeciesClassificationResponse
)
from repositories.plant_registration import (
    create_plant,
    get_user_plants,
    get_plant_by_id,
    update_plant,
    delete_plant,
    get_plant_stats,
    search_plants
)
from clients.species_classification import (
    classify_plant_species,
    get_species_korean_name,
    get_species_info
)
from services.image_service import save_uploaded_image
from utils.security import get_current_user
from db.pool import get_db_connection

router = APIRouter(prefix="/plants", tags=["plant-registration"])

@router.post("/classify-species", response_model=SpeciesClassificationResponse)
async def classify_species_from_image(
    image: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    이미지를 업로드하여 식물 품종을 분류합니다.
    
    - **image**: 분류할 식물 이미지 파일
    """
    try:
        # 파일 유효성 검사
        if not image.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        # 이미지 데이터 읽기
        image_data = await image.read()
        
        # 품종 분류 수행
        result = await classify_plant_species(image_data)
        
        if result.success and result.species:
            # 한국어 품종명 추가
            korean_name = get_species_korean_name(result.species)
            species_info = get_species_info(result.species)
            
            return SpeciesClassificationResponse(
                success=True,
                species=result.species,
                confidence=result.confidence,
                top_predictions=result.top_predictions,
                message=f"분류 완료: {korean_name} (신뢰도: {result.confidence:.1%})"
            )
        else:
            return SpeciesClassificationResponse(
                success=False,
                message=result.message
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"품종 분류 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("", response_model=PlantRegistrationResponse, status_code=201)
async def register_plant(
    plant_name: str = Form(...),
    species: Optional[str] = Form(None),
    meet_day: date = Form(...),
    plant_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    """
    새 식물을 등록합니다.
    
    - **plant_name**: 식물 별명 (필수)
    - **species**: 식물 품종 (선택사항)
    - **meet_day**: 키우기 시작한 날 (필수)
    - **plant_id**: 식물 위키 ID (선택사항)
    - **image**: 식물 이미지 (선택사항)
    """
    try:
        # 이미지가 제공된 경우 품종 분류 수행
        if image and not species:
            image_data = await image.read()
            classification_result = await classify_plant_species(image_data)
            
            if classification_result.success and classification_result.species:
                species = classification_result.species
                # 이미지 저장
                await save_uploaded_image(image, "plants")
        
        # 식물 등록 요청 생성
        plant_request = PlantRegistrationRequest(
            plant_name=plant_name,
            species=species,
            meet_day=meet_day,
            plant_id=plant_id
        )
        
        # 식물 등록
        result = await create_plant(user["user_id"], plant_request)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 등록 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("", response_model=PlantListResponse)
async def get_plants(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    user: dict = Depends(get_current_user)
):
    """
    사용자의 식물 목록을 조회합니다.
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    """
    try:
        result = await get_user_plants(user["user_id"], page, limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/search", response_model=PlantListResponse)
async def search_user_plants(
    q: str = Query(..., min_length=1, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    user: dict = Depends(get_current_user)
):
    """
    식물을 검색합니다.
    
    - **q**: 검색어 (필수) - 식물명 또는 품종에서 검색
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    """
    try:
        result = await search_plants(user["user_id"], q, page, limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 검색 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/stats")
async def get_plant_statistics(
    user: dict = Depends(get_current_user)
):
    """
    사용자의 식물 통계 정보를 조회합니다.
    
    - 전체 식물 수
    - 고유 품종 수
    - 첫 식물 등록일
    - 최근 식물 등록일
    - 인기 품종 TOP 5
    """
    try:
        result = await get_plant_stats(user["user_id"])
        return {
            "user_id": user["user_id"],
            **result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}", response_model=PlantRegistrationResponse)
async def get_plant_detail(
    plant_idx: int,
    user: dict = Depends(get_current_user)
):
    """
    특정 식물의 상세 정보를 조회합니다.
    
    - **plant_idx**: 식물 ID
    """
    try:
        result = await get_plant_by_id(plant_idx, user["user_id"])
        if not result:
            raise HTTPException(
                status_code=404,
                detail="식물을 찾을 수 없습니다."
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 상세 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/{plant_idx}", response_model=PlantUpdateResponse)
async def update_plant_info(
    plant_idx: int,
    plant_name: Optional[str] = Form(None),
    species: Optional[str] = Form(None),
    meet_day: Optional[date] = Form(None),
    plant_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    """
    식물 정보를 수정합니다.
    
    - **plant_idx**: 식물 ID
    - **plant_name**: 식물 별명 (선택사항)
    - **species**: 식물 품종 (선택사항)
    - **meet_day**: 키우기 시작한 날 (선택사항)
    - **plant_id**: 식물 위키 ID (선택사항)
    - **image**: 식물 이미지 (선택사항)
    """
    try:
        # 이미지가 제공된 경우 품종 분류 수행
        if image and not species:
            image_data = await image.read()
            classification_result = await classify_plant_species(image_data)
            
            if classification_result.success and classification_result.species:
                species = classification_result.species
                # 이미지 저장
                await save_uploaded_image(image, "plants")
        
        # 식물 수정 요청 생성
        update_request = PlantUpdateRequest(
            plant_name=plant_name,
            species=species,
            meet_day=meet_day,
            plant_id=plant_id
        )
        
        # 식물 정보 수정
        result = await update_plant(plant_idx, user["user_id"], update_request)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="식물을 찾을 수 없습니다."
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 정보 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/{plant_idx}")
async def delete_plant_info(
    plant_idx: int,
    user: dict = Depends(get_current_user)
):
    """
    식물을 삭제합니다.
    
    - **plant_idx**: 식물 ID
    """
    try:
        success = await delete_plant(plant_idx, user["user_id"])
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="식물을 찾을 수 없습니다."
            )
        
        return {
            "success": True,
            "message": "식물이 성공적으로 삭제되었습니다.",
            "plant_idx": plant_idx
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/{plant_idx}/reclassify", response_model=SpeciesClassificationResponse)
async def reclassify_plant_species(
    plant_idx: int,
    image: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    기존 식물의 품종을 다시 분류합니다.
    
    - **plant_idx**: 식물 ID
    - **image**: 분류할 식물 이미지 파일
    """
    try:
        # 식물 존재 확인
        plant = await get_plant_by_id(plant_idx, user["user_id"])
        if not plant:
            raise HTTPException(
                status_code=404,
                detail="식물을 찾을 수 없습니다."
            )
        
        # 파일 유효성 검사
        if not image.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        # 이미지 데이터 읽기
        image_data = await image.read()
        
        # 품종 분류 수행
        result = await classify_plant_species(image_data)
        
        if result.success and result.species:
            # 한국어 품종명 추가
            korean_name = get_species_korean_name(result.species)
            species_info = get_species_info(result.species)
            
            return SpeciesClassificationResponse(
                success=True,
                species=result.species,
                confidence=result.confidence,
                top_predictions=result.top_predictions,
                message=f"재분류 완료: {korean_name} (신뢰도: {result.confidence:.1%})"
            )
        else:
            return SpeciesClassificationResponse(
                success=False,
                message=result.message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"품종 재분류 중 오류가 발생했습니다: {str(e)}"
        )
