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
    search_plants,
    save_plant_image_to_db
)
from clients.species_classification import (
    classify_plant_species,
    get_species_korean_name,
    get_species_info,
    get_english_species_name
)
from services.image_service import save_uploaded_image
from services.auth_service import get_current_user
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
        print(f"[DEBUG] 품종 분류 API 호출 - 파일명: {image.filename}, 크기: {image.size}")
        
        # 파일 유효성 검사
        if not image.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        # 이미지 데이터 읽기
        image_data = await image.read()
        print(f"[DEBUG] 이미지 데이터 크기: {len(image_data)} bytes")
        print(f"[DEBUG] 이미지 파일명: {image.filename}")
        print(f"[DEBUG] 이미지 Content-Type: {image.content_type}")
        
        # 품종 분류 수행
        print(f"[DEBUG] 모델 서버로 품종 분류 요청 시작")
        result = await classify_plant_species(image_data)
        print(f"[DEBUG] 품종 분류 결과: {result}")
        
        if result.success and result.species:
            # 한국어 품종명 추가
            korean_name = get_species_korean_name(result.species)
            species_info = get_species_info(result.species)
            
            return SpeciesClassificationResponse(
                success=True,
                species=result.species,
                species_korean=korean_name,
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
        print(f"[ERROR] 품종 분류 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"품종 분류 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("", response_model=PlantRegistrationResponse, status_code=201)
async def register_plant(
    plant_name: str = Form(...),
    location: Optional[str] = Form(None),
    species: Optional[str] = Form(None),
    meet_day: date = Form(...),
    plant_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
):
    """
    새 식물을 등록합니다.
    
    - **plant_name**: 식물 별명 (필수)
    - **location**: 식물 위치 (선택사항)
    - **species**: 식물 품종 (선택사항)
    - **meet_day**: 키우기 시작한 날 (필수)
    - **plant_id**: 식물 위키 ID (선택사항)
    - **image**: 식물 이미지 (선택사항)
    """
    try:
        image_url = None
        
        # 이미지가 제공된 경우 처리
        if image:
            # 품종이 없으면 AI 분류 수행
            if not species:
                try:
                    print(f"[DEBUG] 품종 분류 시작 - 이미지 파일: {image.filename}")
                    image_data = await image.read()
                    print(f"[DEBUG] 이미지 데이터 읽기 완료 - 크기: {len(image_data)} bytes")
                    
                    if len(image_data) == 0:
                        print(f"[ERROR] 이미지 데이터가 비어있습니다")
                        raise Exception("이미지 데이터가 비어있습니다")
                    
                    classification_result = await classify_plant_species(image_data)
                    print(f"[DEBUG] 품종 분류 결과: {classification_result}")
                    
                    if classification_result.success and classification_result.species:
                        species = classification_result.species
                        print(f"[DEBUG] 분류된 품종: {species}")
                    else:
                        print(f"[WARNING] 품종 분류 실패: {classification_result.message}")
                        # 품종 분류 실패 시 기본값 설정
                        species = "알 수 없는 품종"
                except Exception as e:
                    print(f"[ERROR] 품종 분류 중 오류: {e}")
                    import traceback
                    print(f"[ERROR] 품종 분류 트레이스백: {traceback.format_exc()}")
                    # 품종 분류 실패해도 식물 등록은 계속 진행
                    species = "알 수 없는 품종"
            
            # 이미지 저장 (품종 분류 여부와 관계없이)
            try:
                image_url = await save_uploaded_image(image, "plants")
                print(f"[DEBUG] 이미지 저장 완료: {image_url}")
            except Exception as e:
                print(f"[ERROR] 이미지 저장 실패: {e}")
                image_url = None
        
        # 식물 등록 요청 생성
        plant_request = PlantRegistrationRequest(
            plant_name=plant_name,
            location=location,
            species=species,
            meet_day=meet_day,
            plant_id=plant_id
        )
        
        print(f"[DEBUG] 식물 등록 요청: {plant_request}")
        print(f"[DEBUG] 사용자 ID: {user['user_id']}")
        
        # 식물 등록
        result = await create_plant(user["user_id"], plant_request)
        print(f"[DEBUG] 식물 등록 성공: {result}")
        
        # 이미지가 있으면 img_address 테이블에 저장
        if image_url:
            print(f"[INFO] 식물 이미지 저장: {image_url}")
            await save_plant_image_to_db(result.idx, image_url)
        
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
    location: Optional[str] = Form(None),
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
    - **location**: 식물 위치 (선택사항)
    - **species**: 식물 품종 (선택사항)
    - **meet_day**: 키우기 시작한 날 (선택사항)
    - **plant_id**: 식물 위키 ID (선택사항)
    - **image**: 식물 이미지 (선택사항)
    """
    try:
        # 이미지가 제공된 경우 처리
        image_url = None
        if image:
            # 품종이 없으면 AI 분류 수행
            if not species:
                image_data = await image.read()
                classification_result = await classify_plant_species(image_data)
                
                if classification_result.success and classification_result.species:
                    # 영어 품종명을 한글로 변환
                    species = get_species_korean_name(classification_result.species)
            
            # 이미지 저장
            image_url = await save_uploaded_image(image, "plants")
        
        # 식물 수정 요청 생성
        update_request = PlantUpdateRequest(
            plant_name=plant_name,
            location=location,
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
        
        # 이미지가 있으면 img_address 테이블에 저장
        if image_url:
            await save_plant_image_to_db(plant_idx, image_url)
        
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
                species_korean=korean_name,
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


@router.get("/{plant_idx}/wiki-info")
async def get_plant_wiki_info(
    plant_idx: int,
    user: dict = Depends(get_current_user)
):
    """
    식물의 위키 정보를 조회합니다.
    """
    try:
        from repositories.plant_registration import get_plant_by_id
        from repositories.plant_wiki import get_plant_wiki_by_species
        
        print(f"[DEBUG] 위키 정보 조회 시작 - plant_idx: {plant_idx}, user: {user.get('user_id', 'unknown')}")
        
        # 식물 정보 조회
        plant = await get_plant_by_id(plant_idx, user["user_id"])
        if not plant:
            print(f"[DEBUG] 식물을 찾을 수 없음 - plant_idx: {plant_idx}")
            raise HTTPException(
                status_code=404,
                detail="식물을 찾을 수 없습니다."
            )
        
        print(f"[DEBUG] 식물 정보: {plant.plant_name}, 품종: {plant.species}")
        
        # 위키 정보 조회 (한글 이름으로 먼저 시도)
        print(f"[DEBUG] 한글 품종명으로 위키 정보 조회: {plant.species}")
        wiki_info = await get_plant_wiki_by_species(plant.species)
        print(f"[DEBUG] 한글 품종명 조회 결과: {wiki_info}")
        
        # 한글 이름으로 찾지 못했으면 영어 이름으로 시도
        if not wiki_info:
            # 영어 이름으로 변환해서 다시 시도
            english_species = get_english_species_name(plant.species)
            print(f"[DEBUG] 영어 품종명으로 변환: {english_species}")
            if english_species:
                wiki_info = await get_plant_wiki_by_species(english_species)
                print(f"[DEBUG] 영어 품종명 조회 결과: {wiki_info}")
        
        return {
            "success": True,
            "plant_info": {
                "plant_id": plant.plant_id,
                "plant_name": plant.plant_name,
                "species": plant.species
            },
            "wiki_info": wiki_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] 식물 위키 정보 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"식물 위키 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )
