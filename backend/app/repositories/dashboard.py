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
    print(f"[DEBUG] get_user_plants_with_status called with user_id: {user_id}")
    async with get_db_connection() as (conn, cursor):
        # 먼저 user_plant 테이블 구조 확인
        print("[DEBUG] Checking user_plant table structure...")
        await cursor.execute("DESCRIBE user_plant")
        table_structure = await cursor.fetchall()
        print(f"[DEBUG] user_plant table structure: {table_structure}")
        
        # 간단한 쿼리로 테스트 (실제 구조에 맞게)
        print("[DEBUG] Testing simple query...")
        await cursor.execute("SELECT plant_id, user_id, plant_name FROM user_plant WHERE user_id = %s LIMIT 1", (user_id,))
        test_result = await cursor.fetchone()
        print(f"[DEBUG] Test query result: {test_result}")
        
        # 실제 데이터베이스 구조에 맞는 쿼리
        simple_query = """
        SELECT 
            up.plant_id,
            up.user_id,
            up.plant_name,
            up.species,
            up.meet_day
        FROM user_plant up
        WHERE up.user_id = %s
        ORDER BY up.meet_day DESC
        """
        
        print(f"[DEBUG] Executing simple query with user_id: {user_id}")
        await cursor.execute(simple_query, (user_id,))
        results = await cursor.fetchall()
        print(f"[DEBUG] Simple query returned {len(results)} results")
        
        plants = []
        for row in results:
            plant = PlantStatusResponse(
                idx=row['plant_id'],  # plant_id가 실제 primary key
                user_id=row['user_id'],
                plant_id=row['plant_id'],
                plant_name=row['plant_name'],
                species=row['species'],
                pest_id=None,
                meet_day=row['meet_day'],
                on=None,  # location은 사용하지 않으므로 None
                current_humidity=None,
                humidity_date=None,
                wiki_img=None,
                feature=None,
                temp=None,
                watering=None,
                pest_cause=None,
                pest_cure=None,
                user_plant_image=None
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
