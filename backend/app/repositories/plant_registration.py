import aiomysql
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from db.pool import get_db_connection
from schemas.plant_registration import (
    PlantRegistrationRequest,
    PlantRegistrationResponse,
    PlantListResponse,
    PlantUpdateRequest,
    PlantUpdateResponse
)

async def create_plant(
    user_id: str,
    plant_request: PlantRegistrationRequest
) -> PlantRegistrationResponse:
    """새 식물을 등록합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            # 식물 등록
            await cursor.execute(
                """
                INSERT INTO user_plant (user_id, plant_name, species, meet_day, plant_id, on, created_at)
                VALUES (%s, %s, %s, %s, %s, 1, NOW())
                """,
                (
                    user_id,
                    plant_request.plant_name,
                    plant_request.species,
                    plant_request.meet_day,
                    plant_request.plant_id
                )
            )
            
            plant_idx = cursor.lastrowid
            
            # 생성된 식물 정보 조회
            await cursor.execute(
                "SELECT * FROM user_plant WHERE idx = %s",
                (plant_idx,)
            )
            result = await cursor.fetchone()
            
            return PlantRegistrationResponse(
                idx=result['idx'],
                user_id=result['user_id'],
                plant_name=result['plant_name'],
                species=result['species'],
                meet_day=result['meet_day'],
                plant_id=result['plant_id'],
                created_at=result['created_at']
            )
            
    except Exception as e:
        print(f"Error in create_plant: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_user_plants(
    user_id: str,
    page: int = 1,
    limit: int = 20
) -> PlantListResponse:
    """사용자의 식물 목록을 조회합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            # 전체 개수 조회
            await cursor.execute(
                "SELECT COUNT(*) as total FROM user_plant WHERE user_id = %s AND on = 1",
                (user_id,)
            )
            count_result = await cursor.fetchone()
            total_count = count_result['total']
            
            # 페이지네이션 계산
            offset = (page - 1) * limit
            
            # 식물 목록 조회
            await cursor.execute(
                """
                SELECT * FROM user_plant 
                WHERE user_id = %s AND on = 1
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset)
            )
            results = await cursor.fetchall()
            
            plants = [
                PlantRegistrationResponse(
                    idx=row['idx'],
                    user_id=row['user_id'],
                    plant_name=row['plant_name'],
                    species=row['species'],
                    meet_day=row['meet_day'],
                    plant_id=row['plant_id'],
                    created_at=row['created_at']
                )
                for row in results
            ]
            
            return PlantListResponse(
                plants=plants,
                total_count=total_count,
                page=page,
                limit=limit,
                has_more=(offset + limit) < total_count
            )
            
    except Exception as e:
        print(f"Error in get_user_plants: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_plant_by_id(plant_idx: int, user_id: str) -> Optional[PlantRegistrationResponse]:
    """특정 식물 정보를 조회합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT * FROM user_plant WHERE idx = %s AND user_id = %s AND on = 1",
                (plant_idx, user_id)
            )
            result = await cursor.fetchone()
            
            if result:
                return PlantRegistrationResponse(
                    idx=result['idx'],
                    user_id=result['user_id'],
                    plant_name=result['plant_name'],
                    species=result['species'],
                    meet_day=result['meet_day'],
                    plant_id=result['plant_id'],
                    created_at=result['created_at']
                )
            return None
            
    except Exception as e:
        print(f"Error in get_plant_by_id: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def update_plant(
    plant_idx: int,
    user_id: str,
    update_request: PlantUpdateRequest
) -> Optional[PlantUpdateResponse]:
    """식물 정보를 수정합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            # 업데이트할 필드 구성
            update_fields = []
            update_values = []
            
            if update_request.plant_name is not None:
                update_fields.append("plant_name = %s")
                update_values.append(update_request.plant_name)
            
            if update_request.species is not None:
                update_fields.append("species = %s")
                update_values.append(update_request.species)
            
            if update_request.meet_day is not None:
                update_fields.append("meet_day = %s")
                update_values.append(update_request.meet_day)
            
            if update_request.plant_id is not None:
                update_fields.append("plant_id = %s")
                update_values.append(update_request.plant_id)
            
            if not update_fields:
                # 업데이트할 필드가 없는 경우
                return await get_plant_by_id(plant_idx, user_id)
            
            # updated_at 추가
            update_fields.append("updated_at = NOW()")
            
            # 쿼리 실행
            update_values.extend([plant_idx, user_id])
            query = f"""
                UPDATE user_plant 
                SET {', '.join(update_fields)}
                WHERE idx = %s AND user_id = %s AND on = 1
            """
            
            await cursor.execute(query, update_values)
            
            if cursor.rowcount > 0:
                # 수정된 식물 정보 조회
                await cursor.execute(
                    "SELECT * FROM user_plant WHERE idx = %s AND user_id = %s",
                    (plant_idx, user_id)
                )
                result = await cursor.fetchone()
                
                return PlantUpdateResponse(
                    idx=result['idx'],
                    user_id=result['user_id'],
                    plant_name=result['plant_name'],
                    species=result['species'],
                    meet_day=result['meet_day'],
                    plant_id=result['plant_id'],
                    updated_at=result['updated_at']
                )
            return None
            
    except Exception as e:
        print(f"Error in update_plant: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def delete_plant(plant_idx: int, user_id: str) -> bool:
    """식물을 삭제합니다 (소프트 삭제)."""
    connection = None
    try:
        connection = await get_db_connection()
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "UPDATE user_plant SET on = 0, updated_at = NOW() WHERE idx = %s AND user_id = %s",
                (plant_idx, user_id)
            )
            
            return cursor.rowcount > 0
            
    except Exception as e:
        print(f"Error in delete_plant: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_plant_stats(user_id: str) -> Dict[str, Any]:
    """사용자의 식물 통계를 조회합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            # 기본 통계 조회
            await cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_plants,
                    COUNT(DISTINCT species) as unique_species,
                    MIN(meet_day) as first_plant_date,
                    MAX(meet_day) as latest_plant_date
                FROM user_plant 
                WHERE user_id = %s AND on = 1
                """,
                (user_id,)
            )
            stats_result = await cursor.fetchone()
            
            # 품종별 통계
            await cursor.execute(
                """
                SELECT 
                    species,
                    COUNT(*) as count
                FROM user_plant 
                WHERE user_id = %s AND on = 1 AND species IS NOT NULL
                GROUP BY species
                ORDER BY count DESC
                LIMIT 5
                """,
                (user_id,)
            )
            species_stats = await cursor.fetchall()
            
            return {
                "total_plants": stats_result['total_plants'],
                "unique_species": stats_result['unique_species'],
                "first_plant_date": stats_result['first_plant_date'],
                "latest_plant_date": stats_result['latest_plant_date'],
                "top_species": [
                    {"species": row['species'], "count": row['count']}
                    for row in species_stats
                ]
            }
            
    except Exception as e:
        print(f"Error in get_plant_stats: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def search_plants(
    user_id: str,
    query: str,
    page: int = 1,
    limit: int = 20
) -> PlantListResponse:
    """식물을 검색합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            search_term = f"%{query}%"
            
            # 전체 개수 조회
            await cursor.execute(
                """
                SELECT COUNT(*) as total 
                FROM user_plant 
                WHERE user_id = %s AND on = 1 
                AND (plant_name LIKE %s OR species LIKE %s)
                """,
                (user_id, search_term, search_term)
            )
            count_result = await cursor.fetchone()
            total_count = count_result['total']
            
            # 페이지네이션 계산
            offset = (page - 1) * limit
            
            # 검색 결과 조회
            await cursor.execute(
                """
                SELECT * FROM user_plant 
                WHERE user_id = %s AND on = 1 
                AND (plant_name LIKE %s OR species LIKE %s)
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, search_term, search_term, limit, offset)
            )
            results = await cursor.fetchall()
            
            plants = [
                PlantRegistrationResponse(
                    idx=row['idx'],
                    user_id=row['user_id'],
                    plant_name=row['plant_name'],
                    species=row['species'],
                    meet_day=row['meet_day'],
                    plant_id=row['plant_id'],
                    created_at=row['created_at']
                )
                for row in results
            ]
            
            return PlantListResponse(
                plants=plants,
                total_count=total_count,
                page=page,
                limit=limit,
                has_more=(offset + limit) < total_count
            )
            
    except Exception as e:
        print(f"Error in search_plants: {e}")
        raise e
    finally:
        if connection:
            connection.close()
