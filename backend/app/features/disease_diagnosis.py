from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional
from datetime import date, datetime
import aiomysql

from schemas.disease_diagnosis import (
    DiseaseDiagnosisResponse,
    UserPlantsResponse,
    UserPlantOption,
    DiseaseDiagnosisSaveRequest,
    DiseaseDiagnosisSaveResponse
)
from clients.disease_diagnosis import diagnose_disease_from_image
from services.image_service import save_uploaded_image
from db.pool import get_db_connection
from utils.security import get_current_user

router = APIRouter(prefix="/disease-diagnosis", tags=["disease-diagnosis"])


@router.post("/diagnose", response_model=DiseaseDiagnosisResponse)
async def diagnose_disease_from_upload(
    image: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    이미지를 업로드하여 병충해를 진단합니다.
    
    - **image**: 진단할 식물 이미지 파일
    """
    try:
        # 파일 유효성 검사
        if not image.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        # 이미지 데이터 읽기
        image_data = await image.read()
        
        # 이미지 저장
        img_url = await save_uploaded_image(image, "disease_diagnosis")
        
        # 병충해 진단 수행
        result = await diagnose_disease_from_image(image_data)
        
        return DiseaseDiagnosisResponse(
            success=result.success,
            message=result.message,
            predictions=result.predictions,
            image_url=img_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/my-plants", response_model=UserPlantsResponse)
async def get_user_plants_for_diagnosis(
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    사용자의 식물 목록을 조회합니다. (병충해 진단용)
    
    내 식물인지 아닌지 선택할 때 사용하는 API입니다.
    """
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """
                SELECT 
                    plant_id,
                    plant_name,
                    species,
                    meet_day
                FROM user_plant 
                WHERE user_id = %s AND on = 1
                ORDER BY plant_name ASC
                """,
                (user["user_id"],)
            )
            results = await cursor.fetchall()
            
            plants = [
                UserPlantOption(
                    plant_id=row["plant_id"],
                    plant_name=row["plant_name"],
                    species=row["species"],
                    meet_day=row["meet_day"]
                )
                for row in results
            ]
            
            return UserPlantsResponse(
                plants=plants,
                total_count=len(plants)
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"사용자 식물 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/save", response_model=DiseaseDiagnosisSaveResponse)
async def save_disease_diagnosis(
    save_request: DiseaseDiagnosisSaveRequest,
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    병충해 진단 결과를 저장합니다.
    
    - **plant_id**: 선택한 식물 ID (선택사항 - None이면 저장하지 않음)
    - **disease_name**: 선택한 병충해 이름
    - **confidence**: 신뢰도
    - **diagnosis_date**: 진단 날짜
    - **image_url**: 진단 이미지 URL
    """
    try:
        # plant_id가 제공된 경우에만 저장
        if save_request.plant_id is None:
            return DiseaseDiagnosisSaveResponse(
                success=True,
                message="식물을 선택하지 않아 저장하지 않았습니다.",
                diagnosis_id=None,
                saved_to_my_plants=False
            )
        
        # 사용자의 식물인지 확인
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT plant_id FROM user_plant WHERE plant_id = %s AND user_id = %s",
                (save_request.plant_id, user["user_id"])
            )
            if not await cursor.fetchone():
                raise HTTPException(
                    status_code=403,
                    detail="해당 식물에 대한 권한이 없습니다."
                )
        
        # 병충해 ID 조회 (pest_wiki 테이블에서)
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT pest_id FROM pest_wiki WHERE pest_name = %s LIMIT 1",
                (save_request.disease_name,)
            )
            pest_result = await cursor.fetchone()
            
            if pest_result:
                pest_id = pest_result["pest_id"]
            else:
                # 병충해가 DB에 없는 경우 기본값 사용
                pest_id = 1  # 기본 병충해 ID
        
        # 진단 기록 저장
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """
                INSERT INTO user_plant_pest (
                    plant_id, 
                    pest_id, 
                    pest_date, 
                    diagnosis_image_url
                ) VALUES (%s, %s, %s, %s)
                """,
                (
                    save_request.plant_id,
                    pest_id,
                    save_request.diagnosis_date,
                    save_request.image_url
                )
            )
            diagnosis_id = cursor.lastrowid
        
        return DiseaseDiagnosisSaveResponse(
            success=True,
            message=f"병충해 진단이 성공적으로 저장되었습니다. (진단 ID: {diagnosis_id})",
            diagnosis_id=diagnosis_id,
            saved_to_my_plants=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 저장 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/recent-diagnoses")
async def get_recent_diagnoses(
    limit: int = 5,
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    최근 병충해 진단 기록을 조회합니다.
    """
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """
                SELECT 
                    upp.idx,
                    upp.plant_id,
                    upp.pest_id,
                    upp.pest_date,
                    up.plant_name,
                    pw.pest_name,
                    pw.cause,
                    pw.cure,
                    upp.diagnosis_image_url
                FROM user_plant_pest upp
                JOIN user_plant up ON upp.plant_id = up.plant_id
                JOIN pest_wiki pw ON upp.pest_id = pw.pest_id
                WHERE up.user_id = %s
                ORDER BY upp.pest_date DESC
                LIMIT %s
                """,
                (user["user_id"], limit)
            )
            results = await cursor.fetchall()
            
            return {
                "success": True,
                "diagnoses": results,
                "total_count": len(results)
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"최근 진단 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )
