from fastapi import APIRouter, HTTPException, Depends
from typing import List
from schemas.plant_detail import PlantDiaryResponse
from schemas.disease_diagnosis import UserPlantOption, UserPlantsResponse
from repositories.plant_detail import get_plant_diaries, get_plant_diary_count, get_plant_recent_diary_summary
from services.auth_service import get_current_user
from db.pool import get_db_connection
import aiomysql

router = APIRouter(prefix="/diary-plants", tags=["diary-plants"])

@router.get("/my-plants", response_model=UserPlantsResponse)
async def get_user_plants_for_diary(
    user: dict = Depends(get_current_user),
    db: tuple = Depends(get_db_connection)
):
    """
    일기 작성/수정 시 사용할 사용자의 식물 목록을 조회합니다.
    """
    try:
        print(f"[DEBUG] get_user_plants_for_diary 호출됨 - user_id: {user['user_id']}")
        
        async with db as (conn, cursor):
            print(f"[DEBUG] DB 연결 성공")
            
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
            print(f"[DEBUG] 쿼리 결과: {results}")
            
            plants = [
                UserPlantOption(
                    plant_id=row["plant_id"],
                    plant_name=row["plant_name"],
                    species=row["species"],
                    meet_day=row["meet_day"]
                )
                for row in results
            ]
            print(f"[DEBUG] 변환된 plants: {plants}")
            
            response = UserPlantsResponse(
                plants=plants,
                total_count=len(plants)
            )
            print(f"[DEBUG] 최종 응답: {response}")
            return response
        
    except Exception as e:
        print(f"[ERROR] get_user_plants_for_diary 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"사용자 식물 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/diaries", response_model=List[PlantDiaryResponse])
async def get_plant_diary_list(plant_idx: int, user_id: str, limit: int = 10):
    """
    특정 식물의 일기 목록을 조회합니다.
    최신 순으로 정렬되어 반환됩니다.
    """
    try:
        diaries = await get_plant_diaries(plant_idx, user_id, limit)
        return diaries
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/diaries/count")
async def get_plant_diary_count_info(plant_idx: int, user_id: str):
    """
    특정 식물의 일기 개수를 조회합니다.
    """
    try:
        count = await get_plant_diary_count(plant_idx, user_id)
        return {
            "plant_idx": plant_idx,
            "user_id": user_id,
            "diary_count": count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 개수 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/diaries/recent")
async def get_plant_recent_diaries(plant_idx: int, user_id: str, limit: int = 3):
    """
    특정 식물의 최근 일기를 조회합니다.
    습도 지수 증가 시 물준날로 기록하는 기능과 연동할 수 있습니다.
    """
    try:
        diaries = await get_plant_diaries(plant_idx, user_id, limit)
        
        # 물주기 관련 일기 필터링 (향후 확장용)
        watering_diaries = [d for d in diaries if "물" in (d.user_content or "") or "watering" in (d.hashtag or "").lower()]
        
        return {
            "plant_idx": plant_idx,
            "user_id": user_id,
            "recent_diaries": diaries,
            "watering_diaries": watering_diaries,
            "total_count": len(diaries),
            "watering_count": len(watering_diaries)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"최근 일기 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{plant_idx}/diaries/summary")
async def get_plant_diary_summary(plant_idx: int, user_id: str):
    """
    특정 식물과 연관된 최근 일기의 제목과 작성 날짜를 조회합니다.
    일기가 없으면 "작성한 일기가 없어요." 메시지를 반환합니다.
    """
    try:
        diary_summary = await get_plant_recent_diary_summary(plant_idx, user_id)
        return diary_summary
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일기 요약 조회 중 오류가 발생했습니다: {str(e)}"
        )
