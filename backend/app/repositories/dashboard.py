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
        # 사용자의 식물 정보와 관련된 모든 정보를 조회하는 복합 쿼리
        query = """
        SELECT 
            up.plant_id as idx,  -- plant_id를 idx로 반환
            up.user_id,
            up.plant_id,
            up.plant_name,
            up.species,
            up.pest_id,
            up.meet_day,
            up.location,
            
            -- 최신 습도 정보
            hi.humidity as current_humidity,
            hi.humid_date as humidity_date,
            
            -- 식물 위키 정보
            pw.wiki_img,
            pw.feature,
            pw.temp,
            pw.watering,
            
            -- 병해충 정보
            pest.cause as pest_cause,
            pest.cure as pest_cure,
            
            -- 사용자 식물 사진 (img_address 테이블의 이미지)
            ia.img_url as user_plant_image
            
        FROM user_plant up
        LEFT JOIN (
            SELECT 
                plant_id,
                humidity,
                humid_date,
                ROW_NUMBER() OVER (PARTITION BY plant_id ORDER BY humid_date DESC) as rn
            FROM humid_info
        ) hi ON up.plant_id = hi.plant_id AND hi.rn = 1
        LEFT JOIN plant_wiki pw ON up.plant_id = pw.wiki_plant_id  -- 올바른 조인
        LEFT JOIN pest_wiki pest ON up.pest_id = pest.pest_id
        LEFT JOIN (
            SELECT 
                plant_id,
                img_url,
                ROW_NUMBER() OVER (PARTITION BY plant_id ORDER BY idx DESC) as rn
            FROM img_address
            WHERE img_url IS NOT NULL AND img_url != ''
        ) ia ON up.plant_id = ia.plant_id AND ia.rn = 1
        WHERE up.user_id = %s
        ORDER BY up.meet_day DESC
        """
        
        await cursor.execute(query, (user_id,))
        results = await cursor.fetchall()
        
        plants = []
        for row in results:
            plant = PlantStatusResponse(
                idx=row['idx'],  # plant_id가 idx로 반환됨
                user_id=row['user_id'],
                plant_id=row['plant_id'],
                plant_name=row['plant_name'],
                species=row['species'],
                pest_id=row['pest_id'],
                meet_day=row['meet_day'],
                on=row.get('location'),  # location을 on으로 매핑
                current_humidity=row['current_humidity'],
                humidity_date=row['humidity_date'],
                wiki_img=row['wiki_img'],
                feature=row['feature'],
                temp=row['temp'],
                watering=row['watering'],
                pest_cause=row['pest_cause'],
                pest_cure=row['pest_cure'],
                user_plant_image=row['user_plant_image']
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
