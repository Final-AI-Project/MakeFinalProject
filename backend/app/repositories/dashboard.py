import aiomysql
from typing import List, Optional
from datetime import datetime
from db.pool import get_db_connection
from schemas.dashboard import PlantStatusResponse, DashboardResponse

async def get_user_plants_with_status(user_id: str) -> DashboardResponse:
    """
    사용자의 모든 식물 정보와 상태를 조회합니다.
    습도 정보와 식물 위키 정보, 병해충 정보를 포함합니다.
    """
    async with get_db_connection() as (conn, cursor):
        
        # 이미지 정보와 습도 정보를 포함한 쿼리
        query = """
        SELECT 
            up.plant_id,
            up.user_id,
            up.plant_name,
            up.species,
            up.meet_day,
            
            -- 사용자 식물 사진 (img_address 테이블의 이미지 - 첫 번째 이미지)
            (SELECT ia.img_url 
             FROM img_address ia 
             WHERE ia.plant_id = up.plant_id 
             ORDER BY ia.img_url 
             LIMIT 1) as user_plant_image,
            
            -- 최근 습도 정보 (device_info와 humid_info 조인)
            (SELECT hi.humidity 
             FROM device_info di 
             JOIN humid_info hi ON di.device_id = hi.device_id 
             WHERE di.plant_id = up.plant_id 
             ORDER BY hi.humid_date DESC 
             LIMIT 1) as current_humidity,
             
            -- 최근 습도 측정 시간
            (SELECT hi.humid_date 
             FROM device_info di 
             JOIN humid_info hi ON di.device_id = hi.device_id 
             WHERE di.plant_id = up.plant_id 
             ORDER BY hi.humid_date DESC 
             LIMIT 1) as humidity_date
            
        FROM user_plant up
        WHERE up.user_id = %s
        ORDER BY up.meet_day DESC
        """
        
        await cursor.execute(query, (user_id,))
        results = await cursor.fetchall()
        
        plants = []
        for row in results:
            # 습도 데이터가 없으면 기본값 50% 사용
            humidity = row['current_humidity'] if row['current_humidity'] is not None else 50
            
            plant = PlantStatusResponse(
                idx=row['plant_id'],  # plant_id가 실제 primary key
                user_id=row['user_id'],
                plant_id=row['plant_id'],
                plant_name=row['plant_name'],
                species=row['species'],
                pest_id=None,
                meet_day=row['meet_day'],
                on=None,  # location은 사용하지 않으므로 None
                current_humidity=humidity,  # 실제 습도 데이터 또는 기본값 50%
                humidity_date=row['humidity_date'],
                wiki_img=None,
                feature=None,
                temp=None,
                watering=None,
                pest_cause=None,
                pest_cure=None,
                user_plant_image=row['user_plant_image']  # 실제 이미지 URL 사용
            )
            plants.append(plant)
        
        return DashboardResponse(
            user_id=user_id,
            total_plants=len(plants),
            plants=plants
        )

async def get_plant_humidity_history(plant_id: int, limit: int = 7) -> List[dict]:
    """
    특정 식물의 최근 습도 기록을 조회합니다.
    """
    async with get_db_connection() as (conn, cursor):
        query = """
        SELECT 
            humidity,
            humid_date
        FROM humid_info
        WHERE plant_id = %s
        ORDER BY humid_date DESC
        LIMIT %s
        """
        
        await cursor.execute(query, (plant_id, limit))
        results = await cursor.fetchall()
        return results

async def get_plant_diary_count(plant_id: int) -> int:
    """
    특정 식물의 일기 개수를 조회합니다.
    """
    async with get_db_connection() as (conn, cursor):
        query = """
        SELECT COUNT(*) as count
        FROM diary d
        JOIN user_plant up ON d.user_id = up.user_id
        WHERE up.plant_id = %s
        """
        
        await cursor.execute(query, (plant_id,))
        result = await cursor.fetchone()
        return result['count'] if result else 0
