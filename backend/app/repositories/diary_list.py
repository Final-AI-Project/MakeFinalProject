import aiomysql
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from db.pool import get_db_connection
from schemas.diary import (
    DiaryListItemResponse,
    DiaryListResponse,
    DiarySearchRequest,
    DiaryStatsResponse
)

async def get_user_diary_list(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    order_by: str = "created_at",
    order_direction: str = "desc",
    search_request: Optional[DiarySearchRequest] = None
) -> DiaryListResponse:
    """사용자의 일기 목록을 조회합니다."""
    async with get_db_connection() as (conn, cursor):
        
        # 정렬 방향 검증
        if order_direction.lower() not in ["asc", "desc"]:
            order_direction = "desc"
        
        # 정렬 기준 검증 및 매핑
        order_mapping = {
            "created_at": "d.created_at",
            "updated_at": "d.updated_at", 
            "plant_nickname": "d.plant_nickname",
            "plant_species": "d.plant_species",
            "user_title": "d.user_title"
        }
        
        order_column = order_mapping.get(order_by, "d.created_at")
        
        # 검색 조건 구성
        where_conditions = ["d.user_id = %s"]
        params = [user_id]
        
        if search_request:
            if search_request.query:
                where_conditions.append("(d.user_title LIKE %s OR d.user_content LIKE %s)")
                search_term = f"%{search_request.query}%"
                params.extend([search_term, search_term])
            
            if search_request.plant_nickname:
                where_conditions.append("d.plant_nickname LIKE %s")
                params.append(f"%{search_request.plant_nickname}%")
            
            if search_request.plant_species:
                where_conditions.append("d.plant_species LIKE %s")
                params.append(f"%{search_request.plant_species}%")
            
            if search_request.start_date:
                where_conditions.append("DATE(d.created_at) >= %s")
                params.append(search_request.start_date)
            
            if search_request.end_date:
                where_conditions.append("DATE(d.created_at) <= %s")
                params.append(search_request.end_date)
            
            if search_request.hashtag:
                where_conditions.append("d.hashtag LIKE %s")
                params.append(f"%{search_request.hashtag}%")
        
        where_clause = " AND ".join(where_conditions)
        
        # 전체 개수 조회
        count_query = f"SELECT COUNT(*) as total FROM diary d WHERE {where_clause}"
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(count_query, params)
            count_result = await cursor.fetchone()
            total_count = count_result['total']
            
            # 페이지네이션 계산
            offset = (page - 1) * limit
            
            # 일기 목록 조회
            list_query = f"""
            SELECT 
                d.idx,
                d.user_title,
                d.user_content,
                d.plant_nickname,
                d.plant_species,
                d.plant_reply,
                d.weather,
                d.weather_icon,
                d.img_url,
                d.hashtag,
                d.created_at,
                d.updated_at
            FROM diary d
            WHERE {where_clause}
            ORDER BY {order_column} {order_direction.upper()}
            LIMIT %s OFFSET %s
            """
            
            list_params = params + [limit, offset]
            await cursor.execute(list_query, list_params)
            results = await cursor.fetchall()
            
            diaries = [DiaryListItemResponse(**result) for result in results]
            
            return DiaryListResponse(
                diaries=diaries,
                total_count=total_count,
                page=page,
                limit=limit,
                has_more=(offset + limit) < total_count
            )

async def search_user_diaries(
    user_id: str,
    query: str,
    page: int = 1,
    limit: int = 20
) -> DiaryListResponse:
    """사용자의 일기를 검색합니다."""
    search_request = DiarySearchRequest(query=query)
    return await get_user_diary_list(
        user_id=user_id,
        page=page,
        limit=limit,
        search_request=search_request
    )

async def get_diary_stats(user_id: str) -> DiaryStatsResponse:
    """사용자의 일기 통계를 조회합니다."""
    async with get_db_connection() as (conn, cursor):
        
        # 기본 통계 조회
        stats_query = """
        SELECT 
            COUNT(*) as total_diaries,
            COUNT(DISTINCT plant_nickname) as total_plants,
            COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as recent_diary_count
        FROM diary 
        WHERE user_id = %s
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(stats_query, (user_id,))
            stats_result = await cursor.fetchone()
            
            # 가장 활발한 식물 조회
            most_active_query = """
            SELECT 
                plant_nickname,
                COUNT(*) as diary_count
            FROM diary 
            WHERE user_id = %s AND plant_nickname IS NOT NULL
            GROUP BY plant_nickname
            ORDER BY diary_count DESC
            LIMIT 1
            """
            
            await cursor.execute(most_active_query, (user_id,))
            most_active_result = await cursor.fetchone()
            
            total_diaries = stats_result['total_diaries']
            total_plants = stats_result['total_plants']
            recent_diary_count = stats_result['recent_diary_count']
            most_active_plant = most_active_result['plant_nickname'] if most_active_result else None
            average_diaries_per_plant = total_diaries / total_plants if total_plants > 0 else 0
            
            return DiaryStatsResponse(
                total_diaries=total_diaries,
                total_plants=total_plants,
                recent_diary_count=recent_diary_count,
                most_active_plant=most_active_plant,
                average_diaries_per_plant=round(average_diaries_per_plant, 2)
            )

async def get_plant_diary_summary(user_id: str) -> List[Dict[str, Any]]:
    """식물별 일기 요약을 조회합니다."""
    async with get_db_connection() as (conn, cursor):
        
        query = """
        SELECT 
            plant_nickname,
            plant_species,
            COUNT(*) as diary_count,
            MAX(created_at) as last_diary_date,
            MIN(created_at) as first_diary_date
        FROM diary 
        WHERE user_id = %s AND plant_nickname IS NOT NULL
        GROUP BY plant_nickname, plant_species
        ORDER BY diary_count DESC
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (user_id,))
            results = await cursor.fetchall()
            
            return [
                {
                    "plant_nickname": row['plant_nickname'],
                    "plant_species": row['plant_species'],
                    "diary_count": row['diary_count'],
                    "last_diary_date": row['last_diary_date'],
                    "first_diary_date": row['first_diary_date']
                }
                for row in results
            ]

async def get_recent_diaries(user_id: str, limit: int = 5) -> List[DiaryListItemResponse]:
    """사용자의 최근 일기를 조회합니다."""
    async with get_db_connection() as (conn, cursor):
        
        query = """
        SELECT 
            d.idx,
            d.user_title,
            d.user_content,
            d.plant_nickname,
            d.plant_species,
            d.plant_reply,
            d.weather,
            d.weather_icon,
            d.img_url,
            d.hashtag,
            d.created_at,
            d.updated_at
        FROM diary d
        WHERE d.user_id = %s
        ORDER BY d.created_at DESC
        LIMIT %s
        """
        
        await cursor.execute(query, (user_id, limit))
        results = await cursor.fetchall()
        
        return [DiaryListItemResponse(**result) for result in results]
