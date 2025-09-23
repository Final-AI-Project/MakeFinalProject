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
from services.auth_service import get_current_user

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
        print(f"[DEBUG] 진단 요청 받음 - 사용자: {user.get('user_id', 'unknown')}")
        
        # 파일 유효성 검사
        if not image.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        print(f"[DEBUG] 업로드된 파일: {image.filename}")
        print(f"[DEBUG] 파일 타입: {image.content_type}")
        
        # 이미지 데이터 읽기
        image_data = await image.read()
        print(f"[DEBUG] 이미지 데이터 크기: {len(image_data)} bytes")
        
        # 이미지 저장
        img_url = await save_uploaded_image(image, "disease_diagnosis")
        print(f"[DEBUG] 저장된 이미지 URL: {img_url}")
        
        # 병충해 진단 수행
        print("[DEBUG] 모델 서버 호출 시작...")
        result = await diagnose_disease_from_image(image_data)
        print(f"[DEBUG] 진단 결과: {result}")
        
        # DiseasePrediction 객체를 딕셔너리로 변환
        disease_predictions_dict = []
        for pred in result.disease_predictions:
            disease_predictions_dict.append({
                "class_name": pred.class_name,
                "confidence": pred.confidence,
                "rank": pred.rank
            })
        
        response = DiseaseDiagnosisResponse(
            success=result.success,
            health_check=result.health_check,
            health_status=result.health_status,
            health_confidence=result.health_confidence,
            message=result.message,
            recommendation=result.recommendation,
            disease_predictions=disease_predictions_dict,  # 딕셔너리 리스트로 전달
            image_url=img_url
        )
        print(f"[DEBUG] 최종 응답: {response}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] 진단 API 오류: {e}")
        import traceback
        print(f"[DEBUG] 트레이스백: {traceback.format_exc()}")
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
                WHERE user_id = %s
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
    plant_id: int = Form(...),
    disease_name: str = Form(...),
    confidence: float = Form(...),
    diagnosis_date: str = Form(...),
    image: Optional[UploadFile] = File(None),
    user: dict = Depends(get_current_user)
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
        print(f"[DEBUG] ===== 진단 결과 저장 요청 시작 =====")
        print(f"[DEBUG] 사용자: {user.get('user_id', 'unknown')}")
        print(f"[DEBUG] 저장 데이터: plant_id={plant_id}, disease_name={disease_name}, confidence={confidence}, diagnosis_date={diagnosis_date}")
        print(f"[DEBUG] 이미지 파일: {image.filename if image else 'None'}")
        print(f"[DEBUG] ======================================")
        
        # 이미지 저장 (있는 경우)
        image_url = None
        if image and image.filename:
            print(f"[DEBUG] 이미지 저장 중: {image.filename}")
            image_url = await save_uploaded_image(image, "disease_diagnosis_save")
            print(f"[DEBUG] 저장된 이미지 URL: {image_url}")
        
        # DB 연결 및 사용자의 식물인지 확인
        async with get_db_connection() as (conn, cursor):
            print(f"[DEBUG] 권한 확인: plant_id={plant_id}, user_id={user['user_id']}")
            await cursor.execute(
                "SELECT plant_id, plant_name FROM user_plant WHERE plant_id = %s AND user_id = %s",
                (plant_id, user["user_id"])
            )
            plant_result = await cursor.fetchone()
            print(f"[DEBUG] 권한 확인 결과: {plant_result}")
            if not plant_result:
                # 사용자의 모든 식물 목록도 출력
                await cursor.execute(
                    "SELECT plant_id, plant_name FROM user_plant WHERE user_id = %s",
                    (user["user_id"],)
                )
                user_plants = await cursor.fetchall()
                print(f"[DEBUG] 사용자의 모든 식물: {user_plants}")
                raise HTTPException(
                    status_code=403,
                    detail=f"해당 식물(ID: {plant_id})에 대한 권한이 없습니다."
                )
            
            # 병충해 ID 조회 (pest_wiki 테이블에서)
            await cursor.execute(
                "SELECT pest_id FROM pest_wiki WHERE pest_name = %s LIMIT 1",
                (disease_name,)
            )
            pest_result = await cursor.fetchone()
            
            if pest_result:
                pest_id_db = pest_result["pest_id"]
                print(f"[DEBUG] 병충해 ID 찾음: {pest_id_db}")
            else:
                # 병충해가 DB에 없는 경우 새로운 병충해 추가
                try:
                    await cursor.execute(
                        """
                        INSERT INTO pest_wiki (pest_name, pathogen, symptom, cause, cure)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            disease_name,
                            "알 수 없음",
                            "위키에 정보가 없습니다.",
                            "위키에 정보가 없습니다.",
                            "위키에 정보가 없습니다."
                        )
                    )
                    pest_id_db = cursor.lastrowid
                    print(f"[DEBUG] 새로운 병충해 추가됨: {disease_name} (ID: {pest_id_db})")
                except Exception as e:
                    print(f"[DEBUG] 병충해 추가 중 오류 발생: {e}")
                    # 중복 키 에러인 경우 다시 조회
                    if "Duplicate entry" in str(e):
                        await cursor.execute(
                            "SELECT pest_id FROM pest_wiki WHERE pest_name = %s LIMIT 1",
                            (disease_name,)
                        )
                        result = await cursor.fetchone()
                        if result:
                            pest_id_db = result["pest_id"]
                            print(f"[DEBUG] 중복된 병충해 발견: {disease_name} (ID: {pest_id_db})")
                        else:
                            raise e
                    else:
                        raise e
            
            # 날짜 문자열을 date 객체로 변환
            from datetime import datetime
            try:
                parsed_date = datetime.strptime(diagnosis_date, "%Y-%m-%d").date()
            except ValueError:
                # 날짜 형식이 잘못된 경우 오늘 날짜 사용
                parsed_date = datetime.now().date()
                print(f"[DEBUG] 날짜 파싱 실패, 오늘 날짜 사용: {parsed_date}")
            
            # 진단 기록 저장 (여러 진단 결과 저장 가능)
            await cursor.execute(
                """
                INSERT INTO user_plant_pest (
                    plant_id, 
                    pest_id, 
                    pest_date
                ) VALUES (%s, %s, %s)
                """,
                (
                    plant_id,
                    pest_id_db,
                    parsed_date
                )
            )
            
            diagnosis_id = cursor.lastrowid
            print(f"[DEBUG] 진단 기록 저장 완료 - 새 ID: {diagnosis_id}")
            
            # TODO: 여러 순위 저장을 위한 diagnosis_ranks 테이블 구현
            # 현재는 1순위만 저장
            
            # 진단 이미지를 img_address 테이블에 저장 (이미지가 있는 경우)
            if image_url:
                print(f"[DEBUG] 진단 이미지 URL 저장 중: {image_url}")
                await cursor.execute(
                    """
                    INSERT INTO img_address (
                        pest_plant_idx,
                        img_url
                    ) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE
                        img_url = VALUES(img_url)
                    """,
                    (
                        diagnosis_id,
                        image_url
                    )
                )
                print(f"[DEBUG] 진단 이미지 URL 저장 완료")
        
        return DiseaseDiagnosisSaveResponse(
            success=True,
            message=f"병충해 진단이 성공적으로 저장되었습니다. (진단 ID: {diagnosis_id})",
            diagnosis_id=diagnosis_id,
            saved_to_my_plants=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] 진단 저장 API 오류: {e}")
        import traceback
        print(f"[DEBUG] 트레이스백: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"병충해 진단 저장 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/pest-info/{pest_name}")
async def get_pest_info(
    pest_name: str,
    db: tuple = Depends(get_db_connection)
):
    """
    병충해 이름으로 상세 정보를 조회합니다.
    """
    try:
        async with db.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """
                SELECT 
                    pest_id,
                    pest_name,
                    cause,
                    cure,
                    description
                FROM pest_wiki 
                WHERE pest_name = %s
                LIMIT 1
                """,
                (pest_name,)
            )
            result = await cursor.fetchone()
            
            if result:
                return {
                    "success": True,
                    "pest_info": {
                        "pest_id": result["pest_id"],
                        "pest_name": result["pest_name"],
                        "cause": result["cause"],
                        "cure": result["cure"],
                        "description": result["description"]
                    }
                }
            else:
                # DB에 없는 경우 기본 정보 반환
                return {
                    "success": True,
                    "pest_info": {
                        "pest_id": None,
                        "pest_name": pest_name,
                        "cause": "정확한 원인을 파악하기 위해 식물 전문가에게 상담하세요.",
                        "cure": "적절한 치료제 사용과 환경 개선이 필요합니다.",
                        "description": f"{pest_name} 병충해가 감지되었습니다."
                    }
                }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 정보 조회 중 오류가 발생했습니다: {str(e)}"
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
