from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime

from schemas.plant_registration import (
    PlantRegistrationRequest, PlantRegistrationResponse, 
    SpeciesClassificationRequest, SpeciesClassificationResponse
)
from repositories.plant_registration import (
    create_plant, get_user_plants, get_plant_by_id, 
    update_plant, delete_plant, save_plant_image_to_db, get_plant_images
)
from clients.species_classification import classify_plant_species
from services.auth_service import get_current_user
from services.image_service import save_uploaded_image

router = APIRouter(prefix="/plants", tags=["plants"])


@router.post("/classify-species", response_model=SpeciesClassificationResponse)
async def classify_species_endpoint(
    image: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    식물 종류 분류
    
    - **image**: 분류할 식물 이미지
    """
    try:
        # 이미지 데이터 읽기
        image_data = await image.read()
        
        # 종류 분류
        result = await classify_plant_species(image_data)
        
        if result.success:
            from clients.species_classification import get_species_korean_name
            return SpeciesClassificationResponse(
                species=result.species,
                confidence=result.confidence,
                species_korean=get_species_korean_name(result.species) if result.species else None
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.message
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 종류 분류 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/", response_model=PlantRegistrationResponse, status_code=201)
async def register_plant_endpoint(
    plant_name: str = Form(...),
    species: str = Form(...),
    meet_day: str = Form(...),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    """
    식물 등록
    
    - **plant_name**: 식물 별명
    - **species**: 식물 종류
    - **meet_day**: 만난 날 (YYYY-MM-DD)
    - **image**: 식물 이미지 (선택)
    """
    try:
        # 이미지 저장
        image_url = None
        if image:
            image_url = await save_uploaded_image(image, "plants")
        
        # 식물 등록 요청 생성
        plant_request = PlantRegistrationRequest(
            plant_name=plant_name,
            species=species,
            meet_day=meet_day,
            plant_id=None  # 새 식물이므로 None
        )
        
        # 식물 등록
        plant = await create_plant(plant_request, user["user_id"])
        
        # 이미지가 있으면 DB에 저장
        if image_url:
            await save_plant_image_to_db(plant.idx, image_url)
        
        return PlantRegistrationResponse(
            idx=plant.idx,
            plant_name=plant.plant_name,
            species=plant.species,
            meet_day=plant.meet_day,
            created_at=plant.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 등록 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/", response_model=List[PlantRegistrationResponse])
async def get_user_plants_endpoint(
    user: dict = Depends(get_current_user)
):
    """
    사용자의 식물 목록 조회
    """
    try:
        plants = await get_user_plants(user["user_id"])
        return plants
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{plant_idx}", response_model=PlantRegistrationResponse)
async def get_plant_detail_endpoint(
    plant_idx: int,
    user: dict = Depends(get_current_user)
):
    """
    특정 식물 상세 조회
    
    - **plant_idx**: 식물 ID
    """
    try:
        plant = await get_plant_by_id(plant_idx, user["user_id"])
        if not plant:
            raise HTTPException(status_code=404, detail="식물을 찾을 수 없습니다.")
        
        return plant
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/{plant_idx}", response_model=PlantRegistrationResponse)
async def update_plant_endpoint(
    plant_idx: int,
    plant_name: Optional[str] = Form(None),
    species: Optional[str] = Form(None),
    meet_day: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    """
    식물 정보 수정
    
    - **plant_idx**: 식물 ID
    - **plant_name**: 식물 별명 (선택)
    - **species**: 식물 종류 (선택)
    - **meet_day**: 만난 날 (선택)
    - **image**: 식물 이미지 (선택)
    """
    try:
        # 이미지 저장
        image_url = None
        if image:
            image_url = await save_uploaded_image(image, "plants")
        
        # 식물 수정 요청 생성
        plant_request = PlantRegistrationRequest(
            plant_name=plant_name,
            species=species,
            meet_day=meet_day,
            plant_id=plant_idx
        )
        
        # 식물 수정
        plant = await update_plant(plant_idx, plant_request, user["user_id"])
        if not plant:
            raise HTTPException(status_code=404, detail="식물을 찾을 수 없습니다.")
        
        # 이미지가 있으면 DB에 저장
        if image_url:
            await save_plant_image_to_db(plant.idx, image_url)
        
        return plant
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/{plant_idx}")
async def delete_plant_endpoint(
    plant_idx: int,
    user: dict = Depends(get_current_user)
):
    """
    식물 삭제
    
    - **plant_idx**: 식물 ID
    """
    try:
        success = await delete_plant(plant_idx, user["user_id"])
        if not success:
            raise HTTPException(status_code=404, detail="식물을 찾을 수 없습니다.")
        
        return {"message": "식물이 성공적으로 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 삭제 중 오류가 발생했습니다: {str(e)}"
        )
