from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime
import aiomysql

from schemas.medical import (
    MedicalDiagnosisListResponse,
    MedicalDiagnosisDetailResponse,
    MedicalDiagnosisCreate,
    MedicalDiagnosisUpdate,
    MedicalStatsResponse
)
from repositories.medical import (
    get_user_medical_diagnoses,
    get_medical_diagnosis_by_id,
    create_medical_diagnosis,
    update_medical_diagnosis,
    delete_medical_diagnosis,
    get_medical_stats,
    get_related_diagnoses
)
from db.pool import get_db_connection
from services.auth_service import get_current_user
from services.image_service import save_uploaded_image

router = APIRouter(prefix="/medical", tags=["medical"])


def _to_list_response(diagnosis) -> MedicalDiagnosisListResponse:
    """MedicalDiagnosis 객체를 MedicalDiagnosisListResponse로 변환"""
    return MedicalDiagnosisListResponse(
        idx=diagnosis.idx,
        plant_id=diagnosis.plant_id,
        pest_id=diagnosis.pest_id,
        pest_date=diagnosis.pest_date,
        plant_name=diagnosis.plant_name,
        pest_name=diagnosis.pest_name,
        cause=diagnosis.cause,
        cure=diagnosis.cure,
        diagnosis_image_url=diagnosis.diagnosis_image_url
    )


def _to_detail_response(diagnosis, related_diagnoses: List = None) -> MedicalDiagnosisDetailResponse:
    """MedicalDiagnosis 객체를 MedicalDiagnosisDetailResponse로 변환"""
    return MedicalDiagnosisDetailResponse(
        idx=diagnosis.idx,
        plant_id=diagnosis.plant_id,
        pest_id=diagnosis.pest_id,
        pest_date=diagnosis.pest_date,
        plant_name=diagnosis.plant_name,
        plant_species=diagnosis.plant_species,
        pest_name=diagnosis.pest_name,
        cause=diagnosis.cause,
        cure=diagnosis.cure,
        meet_day=diagnosis.meet_day,
        diagnosis_image_url=diagnosis.diagnosis_image_url,
        related_diagnoses=[_to_list_response(rel) for rel in related_diagnoses] if related_diagnoses else None
    )


@router.get("/diagnoses", response_model=List[MedicalDiagnosisListResponse])
async def get_medical_diagnoses(
    limit: int = Query(50, ge=1, le=100, description="조회할 진단 기록 수"),
    offset: int = Query(0, ge=0, description="건너뛸 진단 기록 수"),
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    사용자의 모든 병충해 진단 기록을 조회합니다.
    
    - **limit**: 조회할 진단 기록 수 (기본값: 50, 최대: 100)
    - **offset**: 건너뛸 진단 기록 수 (기본값: 0)
    - 최신 진단 날짜 순으로 정렬됩니다.
    """
    try:
        diagnoses = await get_user_medical_diagnoses(
            db=db,
            user_id=user["user_id"],
            limit=limit,
            offset=offset
        )
        return [_to_list_response(diagnosis) for diagnosis in diagnoses]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/diagnoses/{diagnosis_id}", response_model=MedicalDiagnosisDetailResponse)
async def get_medical_diagnosis_detail(
    diagnosis_id: int,
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    특정 병충해 진단 기록의 상세 정보를 조회합니다.
    
    - **diagnosis_id**: 진단 기록 ID
    - 같은 식물의 관련 진단 기록도 함께 반환됩니다.
    """
    try:
        diagnosis = await get_medical_diagnosis_by_id(
            db=db,
            diagnosis_id=diagnosis_id,
            user_id=user["user_id"]
        )
        
        if not diagnosis:
            raise HTTPException(
                status_code=404,
                detail="해당 진단 기록을 찾을 수 없습니다."
            )
        
        # 관련 진단 기록 조회 (같은 식물의 다른 진단들)
        related_diagnoses = await get_related_diagnoses(
            db=db,
            plant_id=diagnosis.plant_id,
            user_id=user["user_id"],
            exclude_id=diagnosis_id,
            limit=5
        )
        
        return _to_detail_response(diagnosis, related_diagnoses)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 상세 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/diagnoses", response_model=MedicalDiagnosisDetailResponse, status_code=201)
async def create_medical_diagnosis_record(
    diagnosis_data: MedicalDiagnosisCreate,
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    새로운 병충해 진단 기록을 생성합니다.
    
    - **plant_id**: 식물 ID
    - **pest_id**: 병충해 ID
    - **pest_date**: 진단 날짜
    """
    try:
        # 사용자의 식물인지 확인
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT plant_id FROM user_plant WHERE plant_id = %s AND user_id = %s",
                (diagnosis_data.plant_id, user["user_id"])
            )
            if not await cursor.fetchone():
                raise HTTPException(
                    status_code=403,
                    detail="해당 식물에 대한 권한이 없습니다."
                )
        
        diagnosis = await create_medical_diagnosis(
            db=db,
            plant_id=diagnosis_data.plant_id,
            pest_id=diagnosis_data.pest_id,
            pest_date=diagnosis_data.pest_date,
            diagnosis_image_url=diagnosis_data.diagnosis_image_url
        )
        
        return _to_detail_response(diagnosis)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 기록 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/diagnoses/with-image", response_model=MedicalDiagnosisDetailResponse, status_code=201)
async def create_medical_diagnosis_with_image(
    plant_id: int = Form(...),
    pest_id: int = Form(...),
    pest_date: str = Form(...),
    image: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    이미지와 함께 새로운 병충해 진단 기록을 생성합니다.
    
    - **plant_id**: 식물 ID
    - **pest_id**: 병충해 ID
    - **pest_date**: 진단 날짜 (YYYY-MM-DD 형식)
    - **image**: 진단 시 찍은 사진
    """
    try:
        # 날짜 파싱
        from datetime import datetime
        try:
            parsed_date = datetime.strptime(pest_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요."
            )
        
        # 사용자의 식물인지 확인
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT plant_id FROM user_plant WHERE plant_id = %s AND user_id = %s",
                (plant_id, user["user_id"])
            )
            if not await cursor.fetchone():
                raise HTTPException(
                    status_code=403,
                    detail="해당 식물에 대한 권한이 없습니다."
                )
        
        # 이미지 저장
        img_url = await save_uploaded_image(image, "medical")
        
        # 진단 기록 생성
        diagnosis = await create_medical_diagnosis(
            db=db,
            plant_id=plant_id,
            pest_id=pest_id,
            pest_date=parsed_date,
            diagnosis_image_url=img_url
        )
        
        return _to_detail_response(diagnosis)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 기록 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/diagnoses/{diagnosis_id}", response_model=MedicalDiagnosisDetailResponse)
async def update_medical_diagnosis_record(
    diagnosis_id: int,
    update_data: MedicalDiagnosisUpdate,
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    병충해 진단 기록을 수정합니다.
    
    - **diagnosis_id**: 진단 기록 ID
    - 수정할 필드만 포함하여 요청하세요.
    """
    try:
        updated_diagnosis = await update_medical_diagnosis(
            db=db,
            diagnosis_id=diagnosis_id,
            user_id=user["user_id"],
            pest_id=update_data.pest_id,
            pest_date=update_data.pest_date,
            diagnosis_image_url=update_data.diagnosis_image_url
        )
        
        if not updated_diagnosis:
            raise HTTPException(
                status_code=404,
                detail="해당 진단 기록을 찾을 수 없습니다."
            )
        
        return _to_detail_response(updated_diagnosis)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 기록 수정 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/diagnoses/{diagnosis_id}")
async def delete_medical_diagnosis_record(
    diagnosis_id: int,
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    병충해 진단 기록을 삭제합니다.
    
    - **diagnosis_id**: 진단 기록 ID
    - 삭제된 기록은 복구할 수 없습니다.
    """
    try:
        success = await delete_medical_diagnosis(
            db=db,
            diagnosis_id=diagnosis_id,
            user_id=user["user_id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="해당 진단 기록을 찾을 수 없습니다."
            )
        
        return {"message": "진단 기록이 성공적으로 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 기록 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/stats", response_model=MedicalStatsResponse)
async def get_medical_statistics(
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    사용자의 병충해 진단 통계를 조회합니다.
    
    - 총 진단 수
    - 진단받은 식물 수
    - 가장 흔한 병충해
    - 최근 7일 진단 수
    - 심각도별 분포
    """
    try:
        stats = await get_medical_stats(db=db, user_id=user["user_id"])
        return MedicalStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/diagnoses/plant/{plant_id}", response_model=List[MedicalDiagnosisListResponse])
async def get_plant_medical_diagnoses(
    plant_id: int,
    limit: int = Query(20, ge=1, le=50, description="조회할 진단 기록 수"),
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    특정 식물의 병충해 진단 기록을 조회합니다.
    
    - **plant_id**: 식물 ID
    - **limit**: 조회할 진단 기록 수 (기본값: 20, 최대: 50)
    """
    try:
        # 특정 식물의 진단 기록만 조회
        diagnoses = await get_related_diagnoses(
            db=db,
            plant_id=plant_id,
            user_id=user["user_id"],
            limit=limit
        )
        return [_to_list_response(diagnosis) for diagnosis in diagnoses]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물별 병충해 진단 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )
