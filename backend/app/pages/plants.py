from fastapi import APIRouter, HTTPException
from typing import List
from schemas.dashboard import DashboardResponse, PlantStatusResponse
from repositories.dashboard import get_user_plants_with_status, get_plant_humidity_history, get_plant_diary_count

router = APIRouter(prefix="/home", tags=["home"])

@router.get("/plants/{user_id}", response_model=DashboardResponse)
async def get_user_plants(user_id: str):
    """
    사용자의 모든 식물 정보와 상태를 조회합니다.
    습도, 식물 위키, 병해충 정보를 포함합니다.
    """
    try:
        result = await get_user_plants_with_status(user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/plants/{user_id}/summary")
async def get_user_plants_summary(user_id: str):
    """
    사용자의 식물 요약 정보를 조회합니다.
    """
    try:
        result = await get_user_plants_with_status(user_id)
        
        # 요약 통계 계산
        total_plants = result.total_plants
        plants_with_pest = len([p for p in result.plants if p.pest_id is not None])
        plants_with_humidity = len([p for p in result.plants if p.current_humidity is not None])
        
        # 평균 습도 계산
        humidity_values = [p.current_humidity for p in result.plants if p.current_humidity is not None]
        avg_humidity = sum(humidity_values) / len(humidity_values) if humidity_values else 0
        
        return {
            "user_id": user_id,
            "total_plants": total_plants,
            "plants_with_pest": plants_with_pest,
            "plants_with_humidity": plants_with_humidity,
            "average_humidity": round(avg_humidity, 2),
            "health_status": "good" if plants_with_pest == 0 else "attention_needed"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"식물 요약 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/plants/{plant_id}/humidity-history")
async def get_plant_humidity_history_endpoint(plant_id: int, limit: int = 7):
    """
    특정 식물의 습도 기록을 조회합니다.
    """
    try:
        history = await get_plant_humidity_history(plant_id, limit)
        return {
            "plant_id": plant_id,
            "humidity_history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"습도 기록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/plants/{plant_id}/diary-count")
async def get_plant_diary_count_endpoint(plant_id: int):
    """
    특정 식물의 일기 개수를 조회합니다.
    """
    try:
        count = await get_plant_diary_count(plant_id)
        return {
            "plant_id": plant_id,
            "diary_count": count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 개수 조회 중 오류가 발생했습니다: {str(e)}"
        )
