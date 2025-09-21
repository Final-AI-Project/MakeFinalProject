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
    try:
        async with get_db_connection() as (conn, cursor):
            # 식물 등록 (plant_id는 auto_increment이므로 제외)
            await cursor.execute(
                """
                INSERT INTO user_plant (user_id, plant_name, species, meet_day)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    user_id,
                    plant_request.plant_name,
                    plant_request.species,
                    plant_request.meet_day
                )
            )
            
            plant_id = cursor.lastrowid
            
            # 생성된 식물 정보 조회
            await cursor.execute(
                "SELECT * FROM user_plant WHERE plant_id = %s",
                (plant_id,)
            )
            result = await cursor.fetchone()
            
            return PlantRegistrationResponse(
                idx=result['plant_id'],  # plant_id가 실제 primary key
                user_id=result['user_id'],
                plant_name=result['plant_name'],
                species=result['species'],
                meet_day=result['meet_day'],
                plant_id=result['plant_id'],
                created_at=result.get('created_at', result.get('meet_day'))
            )
            
    except Exception as e:
        print(f"Error in create_plant: {e}")
        raise e

async def get_user_plants(
    user_id: str,
    page: int = 1,
    limit: int = 20
) -> PlantListResponse:
    """사용자의 식물 목록을 조회합니다."""
    try:
        async with get_db_connection() as (conn, cursor):
            # 전체 개수 조회
            await cursor.execute(
                "SELECT COUNT(*) as total FROM user_plant WHERE user_id = %s",
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
                WHERE user_id = %s
                ORDER BY meet_day DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset)
            )
            results = await cursor.fetchall()
            
            plants = [
                PlantRegistrationResponse(
                    idx=row['plant_id'],  # plant_id를 idx로 반환
                    user_id=row['user_id'],
                    plant_name=row['plant_name'],
                    species=row['species'],
                    meet_day=row['meet_day'],
                    plant_id=row['plant_id'],
                    created_at=row.get('created_at', row.get('meet_day'))
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

async def get_plant_by_id(plant_idx: int, user_id: str) -> Optional[PlantRegistrationResponse]:
    """특정 식물 정보를 조회합니다."""
    try:
        async with get_db_connection() as (conn, cursor):
            await cursor.execute(
                "SELECT * FROM user_plant WHERE plant_id = %s AND user_id = %s",
                (plant_idx, user_id)
            )
            result = await cursor.fetchone()
            
            if result:
                return PlantRegistrationResponse(
                    idx=result['plant_id'],  # plant_id를 idx로 반환
                    user_id=result['user_id'],
                    plant_name=result['plant_name'],
                    species=result['species'],
                    meet_day=result['meet_day'],
                    plant_id=result['plant_id'],
                    created_at=result.get('created_at', result.get('meet_day'))
                )
            return None
            
    except Exception as e:
        print(f"Error in get_plant_by_id: {e}")
        raise e

async def update_plant(
    plant_idx: int,
    user_id: str,
    update_request: PlantUpdateRequest
) -> Optional[PlantUpdateResponse]:
    """식물 정보를 수정합니다."""
    try:
        async with get_db_connection() as (conn, cursor):
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
            
            # updated_at 추가 (컬럼이 있다면)
            # update_fields.append("updated_at = NOW()")
            
            # 쿼리 실행
            update_values.extend([plant_idx, user_id])
            query = f"""
                UPDATE user_plant 
                SET {', '.join(update_fields)}
                WHERE plant_id = %s AND user_id = %s
            """
            
            await cursor.execute(query, update_values)
            
            if cursor.rowcount > 0:
                # 수정된 식물 정보 조회
                await cursor.execute(
                    "SELECT * FROM user_plant WHERE plant_id = %s AND user_id = %s",
                    (plant_idx, user_id)
                )
                result = await cursor.fetchone()
                
                return PlantUpdateResponse(
                    idx=result['plant_id'],  # plant_id를 idx로 반환
                    user_id=result['user_id'],
                    plant_name=result['plant_name'],
                    species=result['species'],
                    meet_day=result['meet_day'],
                    plant_id=result['plant_id'],
                    updated_at=result.get('updated_at', result.get('meet_day'))
                )
            return None
            
    except Exception as e:
        print(f"Error in update_plant: {e}")
        raise e

async def delete_plant(plant_idx: int, user_id: str) -> bool:
    """식물을 삭제합니다."""
    try:
        print(f"[DEBUG] delete_plant 시작 - plant_idx: {plant_idx}, user_id: {user_id}")
        
        async with get_db_connection() as (conn, cursor):
            print(f"[DEBUG] DB 연결 성공")
            
            # 트랜잭션 시작
            await conn.begin()
            print(f"[DEBUG] 트랜잭션 시작")
            
            try:
                # 1. 먼저 식물이 존재하는지 확인 (plant_id만 사용)
                print(f"[DEBUG] 식물 존재 확인 중...")
                await cursor.execute(
                    "SELECT plant_id FROM user_plant WHERE plant_id = %s AND user_id = %s",
                    (plant_idx, user_id)
                )
                plant = await cursor.fetchone()
                print(f"[DEBUG] 식물 조회 결과: {plant}")
                
                if not plant:
                    print(f"[DEBUG] 식물을 찾을 수 없음 - 롤백")
                    await conn.rollback()
                    return False
                
                # 실제 plant_id 값 사용
                actual_plant_id = plant['plant_id']
                print(f"[DEBUG] 실제 plant_id: {actual_plant_id}")
                
                # 2. 관련된 이미지 데이터 삭제 (img_address 테이블에서)
                print(f"[DEBUG] 관련 이미지 데이터 삭제 중...")
                await cursor.execute(
                    "DELETE FROM img_address WHERE plant_id = %s",
                    (actual_plant_id,)
                )
                img_deleted = cursor.rowcount
                print(f"[DEBUG] 삭제된 이미지 수: {img_deleted}")
                
                # 3. 관련된 진단 데이터 삭제 (medical_diagnosis 테이블이 있는 경우에만)
                print(f"[DEBUG] 관련 진단 데이터 삭제 중...")
                try:
                    await cursor.execute(
                        "DELETE FROM medical_diagnosis WHERE plant_id = %s",
                        (actual_plant_id,)
                    )
                    diagnosis_deleted = cursor.rowcount
                    print(f"[DEBUG] 삭제된 진단 수: {diagnosis_deleted}")
                except Exception as e:
                    print(f"[DEBUG] medical_diagnosis 테이블이 없거나 오류 발생: {e}")
                    diagnosis_deleted = 0
                
                # 4. 마지막으로 식물 삭제 (plant_id로 삭제)
                print(f"[DEBUG] 식물 삭제 중...")
                await cursor.execute(
                    "DELETE FROM user_plant WHERE plant_id = %s AND user_id = %s",
                    (plant_idx, user_id)
                )
                plant_deleted = cursor.rowcount
                print(f"[DEBUG] 삭제된 식물 수: {plant_deleted}")
                
                # 트랜잭션 커밋
                await conn.commit()
                print(f"[DEBUG] 트랜잭션 커밋 완료")
                
                return plant_deleted > 0
                
            except Exception as e:
                # 오류 발생 시 롤백
                print(f"[DEBUG] 오류 발생 - 롤백: {e}")
                await conn.rollback()
                raise e
            
    except Exception as e:
        print(f"Error in delete_plant: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise e

async def get_plant_stats(user_id: str) -> Dict[str, Any]:
    """사용자의 식물 통계를 조회합니다."""
    try:
        async with get_db_connection() as (conn, cursor):
            # 기본 통계 조회
            await cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_plants,
                    COUNT(DISTINCT species) as unique_species,
                    MIN(meet_day) as first_plant_date,
                    MAX(meet_day) as latest_plant_date
                FROM user_plant 
                WHERE user_id = %s
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
                WHERE user_id = %s AND species IS NOT NULL
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

async def search_plants(
    user_id: str,
    query: str,
    page: int = 1,
    limit: int = 20
) -> PlantListResponse:
    """식물을 검색합니다."""
    try:
        async with get_db_connection() as (conn, cursor):
            search_term = f"%{query}%"
            
            # 전체 개수 조회
            await cursor.execute(
                """
                SELECT COUNT(*) as total 
                FROM user_plant 
                WHERE user_id = %s 
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
                WHERE user_id = %s 
                AND (plant_name LIKE %s OR species LIKE %s)
                ORDER BY meet_day DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, search_term, search_term, limit, offset)
            )
            results = await cursor.fetchall()
            
            plants = [
                PlantRegistrationResponse(
                    idx=row['plant_id'],  # plant_id를 idx로 반환
                    user_id=row['user_id'],
                    plant_name=row['plant_name'],
                    species=row['species'],
                    meet_day=row['meet_day'],
                    plant_id=row['plant_id'],
                    created_at=row.get('created_at', row.get('meet_day'))
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

async def save_plant_image_to_db(plant_idx: int, image_url: str) -> bool:
    """식물 이미지를 img_address 테이블에 저장합니다."""
    try:
        async with get_db_connection() as (conn, cursor):
            await cursor.execute(
                """
                INSERT INTO img_address (plant_id, img_url)
                VALUES (%s, %s)
                """,
                (plant_idx, image_url)
            )
            return True
    except Exception as e:
        print(f"Error in save_plant_image_to_db: {e}")
        raise e

async def get_plant_images(plant_idx: int) -> List[str]:
    """식물의 이미지 URL 목록을 조회합니다."""
    try:
        async with get_db_connection() as (conn, cursor):
            await cursor.execute(
                """
                SELECT img_url FROM img_address 
                WHERE plant_id = %s
                ORDER BY idx DESC
                """,
                (plant_idx,)
            )
            results = await cursor.fetchall()
            return [row['img_url'] for row in results]
    except Exception as e:
        print(f"Error in get_plant_images: {e}")
        raise e
