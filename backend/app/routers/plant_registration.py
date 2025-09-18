from __future__ import annotations

import aiomysql
from datetime import datetime, date
from typing import Any, Dict, List, Optional
import base64
import io
from PIL import Image

from fastapi import APIRouter, Depends, Query, status, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from core.database import get_db
from crud import user_plant as user_plant_crud
from crud import img_address as img_address_crud
from schemas.plant_registration import (
    SpeciesClassificationRequest,
    SpeciesClassificationResult,
    PlantRegistrationCreate,
    PlantRegistrationOut,
    PlantRegistrationUpdate,
    PlantRegistrationListOut
)
from schemas.user_plant import UserPlantOut

from utils.errors import http_error
from utils.security import get_current_user
from utils.pagination import (
    decode_id_cursor, 
    encode_id_cursor, 
    page_window
)

# ML 모델 클라이언트 임포트 (실제 구현 시)
try:
    from ml.species_classification import classify_plant_species
except ImportError:
    # 개발 환경에서 ML 모델이 없을 때의 대체 함수
    def classify_plant_species(image_data: bytes) -> Dict[str, Any]:
        """개발용 더미 분류 함수"""
        return {
            "species": "몬스테라",
            "confidence": 0.85,
            "is_success": True,
            "message": None
        }

router = APIRouter(prefix="/plant-registration", tags=["plant-registration"])

def _to_out(row) -> PlantRegistrationOut:
    """UserPlant 모델을 PlantRegistrationOut 스키마로 변환"""
    return PlantRegistrationOut(
        plant_id=row.plant_id,
        plant_name=row.plant_name,
        species=row.species,
        meet_day=row.meet_day,
        location=row.location if hasattr(row, 'location') else "미설정",
        is_indoor=row.is_indoor if hasattr(row, 'is_indoor') else True,
        profile_image_url=row.profile_image_url if hasattr(row, 'profile_image_url') else None,
        notes=row.notes if hasattr(row, 'notes') else None,
        created_at=row.created_at if hasattr(row, 'created_at') else datetime.now(),
    )


@router.post("/classify-species", response_model=SpeciesClassificationResult)
async def classify_species(
    file: UploadFile = File(..., description="분류할 식물 이미지"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    품종 분류하기 (사진찍기 or 앨범선택)
    - 이미지를 받아서 ML 모델로 품종 분류
    - 분류 결과와 신뢰도 반환
    """
    try:
        # 이미지 파일 검증
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
        
        # 이미지 데이터 읽기
        image_data = await file.read()
        
        # 이미지 크기 제한 (예: 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="이미지 크기는 10MB 이하여야 합니다.")
        
        # ML 모델로 품종 분류
        classification_result = classify_plant_species(image_data)
        
        # 분류 결과 반환
        return SpeciesClassificationResult(
            species=classification_result.get("species", ""),
            confidence=classification_result.get("confidence", 0.0),
            is_success=classification_result.get("is_success", False),
            message=classification_result.get("message")
        )
        
    except Exception as e:
        print(f"Species classification error: {e}")
        return SpeciesClassificationResult(
            species="",
            confidence=0.0,
            is_success=False,
            message="품종 분류 중 오류가 발생했습니다. 직접 입력해주세요."
        )


@router.post("", response_model=PlantRegistrationOut, status_code=status.HTTP_201_CREATED)
async def register_plant(
    body: PlantRegistrationCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    식물 등록 완료
    - 분류 결과 + 분류 결과 실패 시 직접 입력
    - 내 식물 별명 등록 / 키우기 시작한날
    - 키우는 위치 (장소 + 실내/실외)
    """
    try:
        # 1. 식물 등록 (user_plant 테이블)
        plant_row = await user_plant_crud.create(
            db,
            user_id=user["user_id"],
            plant_name=body.plant_name,
            species=body.species or "미분류",
            meet_day=body.meet_day,
            # 추가 필드들은 user_plant 모델에 맞게 조정 필요
        )
        
        # 2. 품종 분류 이미지를 식물 프로필 이미지로 저장
        # 임시로 diary_id=0으로 설정 (식물 프로필 이미지임을 표시)
        profile_image = await img_address_crud.create(
            db,
            diary_id=0,  # 식물 프로필 이미지임을 표시
            img_url=body.classification_image_url,
            status=1  # 품종분류용/식물 프로필 이미지
        )
        
        # 3. 응답 데이터 구성
        return PlantRegistrationOut(
            plant_id=plant_row.plant_id,
            plant_name=plant_row.plant_name,
            species=plant_row.species,
            meet_day=plant_row.meet_day,
            location=body.location,
            is_indoor=body.is_indoor,
            profile_image_url=body.classification_image_url,
            notes=body.notes,
            created_at=datetime.now(),
        )
        
    except Exception as e:
        print(f"Plant registration error: {e}")
        raise http_error("registration_failed", "식물 등록 중 오류가 발생했습니다.", 500)


@router.get("", response_model=PlantRegistrationListOut)
async def get_registered_plants(
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    등록된 식물 목록 조회
    """
    last_idx = decode_id_cursor(cursor)
    
    # 사용자의 등록된 식물 목록 조회
    rows = await user_plant_crud.list_by_user_cursor(
        db, user_id=user["user_id"], limit=limit, last_idx=last_idx
    )
    
    items, has_more = page_window(list(rows), limit)
    next_cursor = encode_id_cursor(items[-1].idx) if has_more else None
    
    return PlantRegistrationListOut(
        items=[_to_out(r) for r in items],
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=len(rows),
    )


@router.get("/{plant_id}", response_model=PlantRegistrationOut)
async def get_registered_plant(
    plant_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    등록된 식물 상세 조회
    """
    row = await user_plant_crud.get_by_plant_id(db, plant_id)
    if not row or row.user_id != user["user_id"]:
        raise http_error("plant_not_found", "식물을 찾을 수 없습니다.", 404)
    
    return _to_out(row)


@router.patch("/{plant_id}", response_model=PlantRegistrationOut)
async def update_registered_plant(
    plant_id: int,
    body: PlantRegistrationUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    등록된 식물 정보 수정
    """
    row = await user_plant_crud.get_by_plant_id(db, plant_id)
    if not row or row.user_id != user["user_id"]:
        raise http_error("plant_not_found", "식물을 찾을 수 없습니다.", 404)

    fields = body.model_dump(exclude_unset=True)
    if not any(v is not None for v in fields.values()):
        return _to_out(row)

    updated = await user_plant_crud.patch(db, row.idx, **fields)
    return _to_out(updated or row)


@router.delete("/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_registered_plant(
    plant_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
    db: tuple[aiomysql.Connection, aiomysql.DictCursor] = Depends(get_db),
):
    """
    등록된 식물 삭제
    """
    row = await user_plant_crud.get_by_plant_id(db, plant_id)
    if not row or row.user_id != user["user_id"]:
        raise http_error("plant_not_found", "식물을 찾을 수 없습니다.", 404)

    # 식물 삭제
    await user_plant_crud.delete_by_plant_id(db, plant_id)
    
    # 관련 이미지들도 삭제 (선택사항)
    # await img_address_crud.delete_by_plant_id(db, plant_id)
    
    return JSONResponse(status_code=204, content=None)
