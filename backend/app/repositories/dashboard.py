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
        
        # img_address 테이블 구조도 확인
        print("[DEBUG] Checking img_address table structure...")
        await cursor.execute("DESCRIBE img_address")
        img_table_structure = await cursor.fetchall()
        print(f"[DEBUG] img_address table structure: {img_table_structure}")
        
        # 간단한 쿼리로 테스트 (실제 구조에 맞게)
        print("[DEBUG] Testing simple query...")
        await cursor.execute("SELECT plant_id, user_id, plant_name FROM user_plant WHERE user_id = %s LIMIT 1", (user_id,))
        test_result = await cursor.fetchone()
        print(f"[DEBUG] Test query result: {test_result}")
        
        # 이미지 정보를 포함한 쿼리 (plant_id로 조인)
        # Final.sql에 따르면 img_address 테이블에 plant_id 컬럼이 있음
        query = """
        SELECT 
            up.plant_id,
            up.user_id,
            up.plant_name,
            up.species,
            up.meet_day,
            
            -- 사용자 식물 사진 (img_address 테이블의 이미지 - 첫 번째 이미지)
            ia.img_url as user_plant_image
            
        FROM user_plant up
        LEFT JOIN img_address ia ON up.plant_id = ia.plant_id 
            AND ia.img_url IS NOT NULL 
            AND ia.img_url != '' 
            AND ia.plant_id IS NOT NULL
        WHERE up.user_id = %s
        GROUP BY up.plant_id, up.user_id, up.plant_name, up.species, up.meet_day, ia.img_url
        ORDER BY up.meet_day DESC
        """
        
        print(f"[DEBUG] Executing query with user_id: {user_id}")
        await cursor.execute(query, (user_id,))
        results = await cursor.fetchall()
        print(f"[DEBUG] Query returned {len(results)} results")
        for i, row in enumerate(results):
            print(f"[DEBUG] Row {i}: plant_id={row['plant_id']}, plant_name={row['plant_name']}, user_plant_image={row['user_plant_image']}")
        
        # img_address 테이블에 실제 데이터가 있는지 확인
        print("[DEBUG] img_address 테이블 데이터 확인...")
        await cursor.execute("SELECT COUNT(*) as total FROM img_address WHERE plant_id IS NOT NULL")
        img_count = await cursor.fetchone()
        print(f"[DEBUG] img_address 테이블의 plant_id가 있는 레코드 수: {img_count['total']}")
        
        if img_count['total'] > 0:
            await cursor.execute("SELECT plant_id, img_url FROM img_address WHERE plant_id IS NOT NULL LIMIT 5")
            sample_imgs = await cursor.fetchall()
            print(f"[DEBUG] img_address 샘플 데이터: {sample_imgs}")
        
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
