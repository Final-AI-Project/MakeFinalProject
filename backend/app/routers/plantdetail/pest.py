from fastapi import APIRouter, HTTPException
from typing import List
from ...schemas.plant_detail import (
    PlantPestRecordResponse, 
    HealthStatusResponse, 
    HealthAnalysisRequest,
    PlantPestRecordRequest,
    PlantPestRecordAddResponse
)
from ...crud.plant_detail import (
    get_plant_pest_records, 
    get_plant_humidity_history,
    analyze_plant_health,
    get_plant_pest_records_by_user_plant,
    add_plant_pest_record
)

router = APIRouter(prefix="/plant-detail", tags=["plant-detail-pest"])

@router.get("/{plant_idx}/pest-records", response_model=List[PlantPestRecordResponse])
async def get_plant_pest_record_list(plant_idx: int, user_id: str):
    """
    특정 식물의 병해충 기록을 조회합니다.
    """
    try:
        pest_records = await get_plant_pest_records(plant_idx, user_id)
        return pest_records
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병해충 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/humidity-history")
async def get_plant_humidity_history_info(plant_idx: int, user_id: str, limit: int = 7):
    """
    특정 식물의 습도 기록을 조회합니다.
    습도 지수 n% 증가 시 물준날로 기록하는 기능과 연동할 수 있습니다.
    """
    try:
        humidity_history = await get_plant_humidity_history(plant_idx, user_id, limit)
        
        # 습도 변화 분석
        humidity_analysis = {
            "current_humidity": humidity_history[0]['humidity'] if humidity_history else None,
            "previous_humidity": humidity_history[1]['humidity'] if len(humidity_history) > 1 else None,
            "trend": "stable",
            "change_percentage": 0
        }
        
        if len(humidity_history) >= 2:
            current = humidity_history[0]['humidity']
            previous = humidity_history[1]['humidity']
            change_percentage = ((current - previous) / previous) * 100 if previous != 0 else 0
            
            humidity_analysis.update({
                "trend": "increasing" if change_percentage > 0 else "decreasing" if change_percentage < 0 else "stable",
                "change_percentage": round(change_percentage, 2)
            })
        
        return {
            "plant_idx": plant_idx,
            "user_id": user_id,
            "humidity_history": humidity_history,
            "humidity_analysis": humidity_analysis,
            "count": len(humidity_history),
            "suggestion": "습도가 10% 이상 증가했다면 물을 준 것으로 기록할 수 있습니다." if humidity_analysis.get("change_percentage", 0) > 10 else "습도 변화가 미미합니다."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"습도 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/health-status", response_model=HealthStatusResponse)
async def get_plant_health_status(plant_idx: int, user_id: str, leaf_health_score: float = None):
    """
    식물의 종합적인 건강상태를 분석합니다.
    습도, 병해충, 잎 건강상태를 종합하여 "건강", "주의", "아픔"으로 판단합니다.
    """
    try:
        health_status = await analyze_plant_health(plant_idx, user_id, leaf_health_score)
        return health_status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"건강 상태 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/{plant_idx}/health-analysis", response_model=HealthStatusResponse)
async def analyze_plant_health_with_ai(plant_idx: int, user_id: str, analysis_request: HealthAnalysisRequest):
    """
    AI 모델 결과를 포함하여 식물의 건강상태를 분석합니다.
    """
    try:
        # 요청의 plant_idx와 user_id가 일치하는지 확인
        if analysis_request.plant_idx != plant_idx or analysis_request.user_id != user_id:
            raise HTTPException(status_code=400, detail="요청 정보가 일치하지 않습니다.")
        
        health_status = await analyze_plant_health(
            plant_idx, 
            user_id, 
            analysis_request.leaf_health_score
        )
        return health_status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 기반 건강 상태 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/health-summary")
async def get_plant_health_summary(plant_idx: int, user_id: str):
    """
    식물의 건강상태 요약 정보를 조회합니다.
    """
    try:
        # 종합 건강상태 분석
        health_status = await analyze_plant_health(plant_idx, user_id)
        
        # 병해충 기록 조회
        pest_records = await get_plant_pest_records(plant_idx, user_id)
        
        # 습도 기록 조회
        humidity_history = await get_plant_humidity_history(plant_idx, user_id, limit=3)
        
        # 건강 상태 등급별 색상 및 아이콘
        status_info = {
            "건강": {"color": "green", "icon": "🌱", "message": "식물이 건강합니다!"},
            "주의": {"color": "yellow", "icon": "⚠️", "message": "식물 관리에 주의가 필요합니다."},
            "아픔": {"color": "red", "icon": "🚨", "message": "식물이 아픈 상태입니다. 즉시 관리가 필요합니다."}
        }
        
        current_status_info = status_info.get(health_status.overall_status, status_info["주의"])
        
        return {
            "plant_idx": plant_idx,
            "user_id": user_id,
            "overall_status": health_status.overall_status,
            "health_score": health_status.health_score,
            "status_info": current_status_info,
            "humidity_status": health_status.humidity_status,
            "pest_status": health_status.pest_status,
            "leaf_health_status": health_status.leaf_health_status,
            "recommendations": health_status.recommendations,
            "urgent_actions": health_status.urgent_actions,
            "pest_count": len(pest_records),
            "last_humidity": humidity_history[0]['humidity'] if humidity_history else None,
            "last_humidity_date": humidity_history[0]['humid_date'] if humidity_history else None,
            "analysis_timestamp": health_status.status_details
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"건강상태 요약 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/pest-records/user-plant", response_model=List[PlantPestRecordResponse])
async def get_user_plant_pest_records(plant_idx: int, user_id: str):
    """
    특정 유저의 특정 식물에 대한 병충해 기록을 조회합니다.
    유저 ID와 식물 ID로 검색하여 해당 식물이 가졌었던 병충해 기록을 반환합니다.
    """
    try:
        pest_records = await get_plant_pest_records_by_user_plant(plant_idx, user_id)
        return pest_records
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/{plant_idx}/pest-records", response_model=PlantPestRecordAddResponse)
async def add_plant_pest_record_endpoint(plant_idx: int, user_id: str, pest_request: PlantPestRecordRequest):
    """
    식물에 병충해 기록을 추가합니다.
    """
    try:
        # 요청의 plant_idx와 user_id가 일치하는지 확인
        if pest_request.plant_idx != plant_idx or pest_request.user_id != user_id:
            raise HTTPException(status_code=400, detail="요청 정보가 일치하지 않습니다.")
        
        # 날짜 형식 검증 (YYYY-MM-DD)
        if pest_request.pest_date:
            try:
                from datetime import datetime
                datetime.strptime(pest_request.pest_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식을 사용해주세요.")
        
        result = await add_plant_pest_record(plant_idx, user_id, pest_request.pest_id, pest_request.pest_date)
        return PlantPestRecordAddResponse(**result)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"병충해 기록 추가 중 오류가 발생했습니다: {str(e)}"
        )
