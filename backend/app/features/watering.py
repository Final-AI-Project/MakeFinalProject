from fastapi import APIRouter, HTTPException
from typing import List
from schemas.plant_detail import (
    WateringRecordResponse, 
    WateringRecordRequest,
    WateringSettingsRequest,
    WateringSettingsResponse,
    WateringPredictionRequest,
    WateringPredictionResponse
)
from repositories.plant_detail import (
    check_humidity_increase_and_record_watering,
    get_watering_records,
    record_manual_watering,
    update_watering_settings,
    get_watering_settings
)
from clients.humidity_prediction import humidity_client
from services.auth_service import get_current_user
from fastapi import Depends
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plant-detail", tags=["plant-detail-watering"])

def calculate_default_watering_time(current_humidity: float, min_humidity: float, temperature: float) -> float:
    """
    습도 모델 서버 연결 실패 시 사용하는 기본 급수 시간 계산 로직
    """
    # 현재 습도가 최소 습도보다 낮으면 즉시 급수 필요
    if current_humidity < min_humidity:
        return 0.5  # 30분 후
    
    # 습도 차이에 따른 기본 계산
    humidity_diff = current_humidity - min_humidity
    
    # 온도 보정 (온도가 높을수록 물이 빨리 증발)
    temp_factor = 1.0 + (temperature - 20) * 0.05  # 20도 기준
    
    # 기본 시간 계산 (습도가 낮을수록 빨리 급수 필요)
    if humidity_diff < 10:
        base_hours = 12  # 12시간
    elif humidity_diff < 20:
        base_hours = 24  # 24시간
    elif humidity_diff < 30:
        base_hours = 48  # 48시간
    else:
        base_hours = 72  # 72시간
    
    # 온도 보정 적용
    adjusted_hours = base_hours / temp_factor
    
    return max(0.5, adjusted_hours)  # 최소 30분

@router.post("/{plant_idx}/check-humidity-watering")
async def check_humidity_and_record_watering(plant_idx: int, user_id: str):
    """
    습도 증가를 확인하고 10% 이상 증가 시 자동으로 물주기 기록을 생성합니다.
    """
    try:
        result = await check_humidity_increase_and_record_watering(plant_idx, user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"습도 확인 및 물주기 기록 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/watering-records", response_model=List[WateringRecordResponse])
async def get_plant_watering_records(plant_idx: int, user_id: str, limit: int = 10):
    """
    특정 식물의 물주기 기록을 조회합니다.
    """
    try:
        watering_records = await get_watering_records(plant_idx, user_id, limit)
        return watering_records
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"물주기 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/{plant_idx}/watering-records", response_model=WateringRecordResponse)
async def create_manual_watering_record(plant_idx: int, user_id: str, watering_request: WateringRecordRequest):
    """
    수동으로 물주기 기록을 생성합니다.
    """
    try:
        # 요청의 plant_idx와 user_id가 일치하는지 확인
        if watering_request.plant_idx != plant_idx or watering_request.user_id != user_id:
            raise HTTPException(status_code=400, detail="요청 정보가 일치하지 않습니다.")
        
        watering_record = await record_manual_watering(plant_idx, user_id, watering_request)
        return watering_record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"물주기 기록 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/watering-summary")
async def get_watering_summary(plant_idx: int, user_id: str):
    """
    식물의 물주기 요약 정보를 조회합니다.
    """
    try:
        # 최근 물주기 기록 조회
        watering_records = await get_watering_records(plant_idx, user_id, limit=5)
        
        # 습도 증가 확인
        humidity_check = await check_humidity_increase_and_record_watering(plant_idx, user_id)
        
        # 통계 계산
        total_watering = len(watering_records)
        auto_watering = len([r for r in watering_records if r.is_auto_detected])
        manual_watering = total_watering - auto_watering
        
        # 최근 물주기 날짜
        last_watering_date = watering_records[0].watering_date if watering_records else None
        
        return {
            "plant_idx": plant_idx,
            "user_id": user_id,
            "total_watering_count": total_watering,
            "auto_watering_count": auto_watering,
            "manual_watering_count": manual_watering,
            "last_watering_date": last_watering_date,
            "humidity_check_result": humidity_check,
            "recent_watering_records": watering_records[:3]  # 최근 3개만
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"물주기 요약 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/watering-status")
async def get_watering_status(plant_idx: int, user_id: str):
    """
    식물의 물주기 상태를 확인합니다.
    """
    try:
        # 습도 증가 확인
        humidity_check = await check_humidity_increase_and_record_watering(plant_idx, user_id)
        
        # 최근 물주기 기록 조회
        recent_watering = await get_watering_records(plant_idx, user_id, limit=1)
        
        # 물주기 필요성 판단
        needs_watering = False
        watering_recommendation = ""
        
        if humidity_check["status"] == "watering_recorded":
            watering_recommendation = "최근에 물을 주었습니다."
        elif humidity_check["status"] == "no_watering_needed":
            if humidity_check.get("humidity_increase", 0) < 5:
                needs_watering = True
                watering_recommendation = "습도가 낮습니다. 물을 주세요."
            else:
                watering_recommendation = "습도 상태가 양호합니다."
        else:
            watering_recommendation = "습도 데이터가 부족합니다."
        
        return {
            "plant_idx": plant_idx,
            "user_id": user_id,
            "needs_watering": needs_watering,
            "watering_recommendation": watering_recommendation,
            "humidity_check": humidity_check,
            "last_watering": recent_watering[0] if recent_watering else None,
            "status": "good" if not needs_watering else "needs_attention"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"물주기 상태 확인 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/watering-settings", response_model=WateringSettingsResponse)
async def get_plant_watering_settings(plant_idx: int, user_id: str):
    """
    식물의 현재 물주기 설정을 조회합니다.
    습도 증가율 임계값을 확인할 수 있습니다.
    """
    try:
        settings = await get_watering_settings(plant_idx, user_id)
        return settings
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"물주기 설정 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/{plant_idx}/watering-settings", response_model=WateringSettingsResponse)
async def update_plant_watering_settings(plant_idx: int, user_id: str, settings_request: WateringSettingsRequest):
    """
    식물의 물주기 설정을 업데이트합니다.
    습도 증가율 임계값을 설정할 수 있습니다.
    """
    try:
        # 요청의 plant_idx와 user_id가 일치하는지 확인
        if settings_request.plant_idx != plant_idx or settings_request.user_id != user_id:
            raise HTTPException(status_code=400, detail="요청 정보가 일치하지 않습니다.")
        
        # 임계값 범위 검증 (5-20% 사이)
        if not (5 <= settings_request.humidity_threshold <= 20):
            raise HTTPException(status_code=400, detail="습도 증가율 임계값은 5%에서 20% 사이여야 합니다.")
        
        settings = await update_watering_settings(plant_idx, user_id, settings_request)
        return settings
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"물주기 설정 업데이트 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/{plant_idx}/watering-prediction", response_model=WateringPredictionResponse)
async def predict_next_watering(plant_idx: int, prediction_request: WateringPredictionRequest, user: dict = Depends(get_current_user)):
    """
    습도 모델을 사용하여 다음 급수 시기를 예측합니다.
    """
    try:
        user_id = user.get("user_id")
        logger.info(f"급수 예측 요청 - 식물 ID: {plant_idx}, 사용자: {user_id}")
        
        # 현재 시간 계산
        current_time = datetime.now()
        hour_of_day = current_time.hour + current_time.minute / 60.0
        
        # 프론트엔드에서 받은 온도 사용 (기본값: 20도)
        temperature = prediction_request.temperature
        
        # 습도 예측 모델 호출
        # 기본 최소 습도 임계값 (식물별로 다를 수 있음)
        min_humidity = 30.0  # 기본값, 실제로는 식물별 최적값 사용
        
        try:
            prediction_result = await humidity_client.predict_watering_time(
                current_humidity=prediction_request.current_humidity,
                min_humidity=min_humidity,
                temperature=temperature,
                hour_of_day=hour_of_day
            )
            
            # 예측 결과에서 시간 추출
            eta_hours = prediction_result.get("eta_h", 24.0)  # 기본값: 24시간
        except Exception as model_error:
            logger.warning(f"습도 모델 서버 연결 실패, 기본값 사용: {str(model_error)}")
            # 모델 서버 연결 실패 시 기본 예측 로직 사용
            eta_hours = calculate_default_watering_time(
                prediction_request.current_humidity, 
                min_humidity, 
                temperature
            )
        
        # 다음 급수 날짜 계산
        next_watering_date = humidity_client.calculate_next_watering_date(eta_hours)
        
        logger.info(f"급수 예측 완료 - 예상 시간: {eta_hours}시간, 다음 급수: {next_watering_date}")
        
        return WateringPredictionResponse(
            success=True,
            plant_idx=plant_idx,
            current_humidity=prediction_request.current_humidity,
            predicted_hours=eta_hours,
            next_watering_date=next_watering_date,
            message=f"다음 급수 예상 시기: {next_watering_date}"
        )
        
    except Exception as e:
        logger.error(f"급수 예측 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"급수 예측 중 오류가 발생했습니다: {str(e)}"
        )
