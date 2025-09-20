from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import aiomysql
from core.database import get_db_connection
from schemas.diary import DiaryListResponse, DiarySearchRequest, DiaryStatsResponse, DiaryListItemResponse


async def get_user_diary_list(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    order_by: str = "created_at",
    order_direction: str = "desc",
    plant_nickname: Optional[str] = None,
    plant_species: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    hashtag: Optional[str] = None
) -> DiaryListResponse:
    """사용자의 일기 목록 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            # 기본 쿼리 구성
            base_query = """
                SELECT d.*, ia.img_url as diary_img_url
                FROM diary d
                LEFT JOIN img_address ia ON d.diary_id = ia.diary_id
                WHERE d.user_id = %s
            """
            params = [user_id]
            
            # 필터 조건 추가
            if plant_nickname:
                base_query += " AND d.plant_nickname LIKE %s"
                params.append(f"%{plant_nickname}%")
            
            if plant_species:
                base_query += " AND d.plant_species LIKE %s"
                params.append(f"%{plant_species}%")
            
            if start_date:
                base_query += " AND d.created_at >= %s"
                params.append(start_date)
            
            if end_date:
                base_query += " AND d.created_at <= %s"
                params.append(end_date)
            
            if hashtag:
                base_query += " AND d.hashtag LIKE %s"
                params.append(f"%{hashtag}%")
            
            # 정렬 조건 추가
            valid_order_fields = ["created_at", "updated_at", "plant_nickname", "plant_species", "user_title"]
            if order_by not in valid_order_fields:
                order_by = "created_at"
            
            valid_directions = ["asc", "desc"]
            if order_direction not in valid_directions:
                order_direction = "desc"
            
            base_query += f" ORDER BY d.{order_by} {order_direction.upper()}"
            
            # 전체 개수 조회
            count_query = base_query.replace("SELECT d.*, ia.img_url as diary_img_url", "SELECT COUNT(*)")
            await cursor.execute(count_query, params)
            total_count = (await cursor.fetchone())["COUNT(*)"]
            
            # 페이지네이션 추가
            offset = (page - 1) * limit
            base_query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # 데이터 조회
            await cursor.execute(base_query, params)
            results = await cursor.fetchall()
            
            # DiaryListItemResponse로 변환
            diaries = []
            for row in results:
                diary = DiaryListItemResponse(
                    idx=row["diary_id"],
                    user_title=row["user_title"],
                    user_content=row["user_content"],
                    plant_nickname=row.get("plant_nickname"),
                    plant_species=row.get("plant_species"),
                    plant_reply=row.get("plant_content"),
                    weather=row.get("weather"),
                    weather_icon=row.get("weather_icon"),
                    img_url=row.get("diary_img_url"),
                    hashtag=row.get("hashtag"),
                    created_at=row["created_at"],
                    updated_at=row.get("updated_at")
                )
                diaries.append(diary)
            
            return DiaryListResponse(
                diaries=diaries,
                total_count=total_count,
                page=page,
                limit=limit,
                has_more=(offset + limit) < total_count
            )
            
        except Exception as e:
            raise Exception(f"일기 목록 조회 중 오류: {str(e)}")


async def search_user_diaries(
    user_id: str,
    request: DiarySearchRequest,
    page: int = 1,
    limit: int = 20
) -> DiaryListResponse:
    """일기 검색"""
    async with get_db_connection() as (conn, cursor):
        try:
            # 검색 쿼리 구성
            search_query = """
                SELECT d.*, ia.img_url as diary_img_url
                FROM diary d
                LEFT JOIN img_address ia ON d.diary_id = ia.diary_id
                WHERE d.user_id = %s
            """
            params = [user_id]
            
            # 검색 조건 추가
            if request.query:
                search_query += " AND (d.user_title LIKE %s OR d.user_content LIKE %s)"
                search_term = f"%{request.query}%"
                params.extend([search_term, search_term])
            
            if request.plant_nickname:
                search_query += " AND d.plant_nickname LIKE %s"
                params.append(f"%{request.plant_nickname}%")
            
            if request.plant_species:
                search_query += " AND d.plant_species LIKE %s"
                params.append(f"%{request.plant_species}%")
            
            if request.start_date:
                search_query += " AND d.created_at >= %s"
                params.append(request.start_date)
            
            if request.end_date:
                search_query += " AND d.created_at <= %s"
                params.append(request.end_date)
            
            if request.hashtag:
                search_query += " AND d.hashtag LIKE %s"
                params.append(f"%{request.hashtag}%")
            
            search_query += " ORDER BY d.created_at DESC"
            
            # 전체 개수 조회
            count_query = search_query.replace("SELECT d.*, ia.img_url as diary_img_url", "SELECT COUNT(*)")
            await cursor.execute(count_query, params)
            total_count = (await cursor.fetchone())["COUNT(*)"]
            
            # 페이지네이션 추가
            offset = (page - 1) * limit
            search_query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # 데이터 조회
            await cursor.execute(search_query, params)
            results = await cursor.fetchall()
            
            # DiaryListItemResponse로 변환
            diaries = []
            for row in results:
                diary = DiaryListItemResponse(
                    idx=row["diary_id"],
                    user_title=row["user_title"],
                    user_content=row["user_content"],
                    plant_nickname=row.get("plant_nickname"),
                    plant_species=row.get("plant_species"),
                    plant_reply=row.get("plant_content"),
                    weather=row.get("weather"),
                    weather_icon=row.get("weather_icon"),
                    img_url=row.get("diary_img_url"),
                    hashtag=row.get("hashtag"),
                    created_at=row["created_at"],
                    updated_at=row.get("updated_at")
                )
                diaries.append(diary)
            
            return DiaryListResponse(
                diaries=diaries,
                total_count=total_count,
                page=page,
                limit=limit,
                has_more=(offset + limit) < total_count
            )
            
        except Exception as e:
            raise Exception(f"일기 검색 중 오류: {str(e)}")


async def get_diary_stats(user_id: str) -> DiaryStatsResponse:
    """일기 통계 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            # 전체 일기 수
            await cursor.execute("SELECT COUNT(*) as total FROM diary WHERE user_id = %s", (user_id,))
            total_diaries = (await cursor.fetchone())["total"]
            
            # 최근 7일 일기 수
            await cursor.execute("""
                SELECT COUNT(*) as recent 
                FROM diary 
                WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """, (user_id,))
            recent_diaries = (await cursor.fetchone())["recent"]
            
            # 가장 활발한 식물
            await cursor.execute("""
                SELECT plant_species, COUNT(*) as count
                FROM diary 
                WHERE user_id = %s AND plant_species IS NOT NULL
                GROUP BY plant_species
                ORDER BY count DESC
                LIMIT 1
            """, (user_id,))
            most_active = await cursor.fetchone()
            
            # 식물 수
            await cursor.execute("""
                SELECT COUNT(DISTINCT plant_species) as plant_count
                FROM diary 
                WHERE user_id = %s AND plant_species IS NOT NULL
            """, (user_id,))
            plant_count = (await cursor.fetchone())["plant_count"]
            
            return DiaryStatsResponse(
                total_diaries=total_diaries,
                total_plants=plant_count,
                recent_diary_count=recent_diaries,
                most_active_plant=most_active["plant_species"] if most_active else None,
                average_diaries_per_plant=total_diaries / plant_count if plant_count > 0 else 0.0
            )
            
        except Exception as e:
            raise Exception(f"일기 통계 조회 중 오류: {str(e)}")


async def get_plant_diary_summary(plant_id: int, user_id: str) -> Dict[str, Any]:
    """식물별 일기 요약"""
    async with get_db_connection() as (conn, cursor):
        try:
            await cursor.execute("""
                SELECT 
                    COUNT(*) as diary_count,
                    MAX(created_at) as last_diary_date,
                    AVG(CASE WHEN hist_watered = 1 THEN 1 ELSE 0 END) as watering_frequency
                FROM diary 
                WHERE user_id = %s AND plant_id = %s
            """, (user_id, plant_id))
            
            result = await cursor.fetchone()
            return dict(result) if result else {}
            
        except Exception as e:
            raise Exception(f"식물 일기 요약 조회 중 오류: {str(e)}")


async def get_recent_diaries(user_id: str, limit: int = 5) -> List[DiaryListItemResponse]:
    """최근 일기 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            query = """
                SELECT d.*, ia.img_url as diary_img_url
                FROM diary d
                LEFT JOIN img_address ia ON d.diary_id = ia.diary_id
                WHERE d.user_id = %s
                ORDER BY d.created_at DESC
                LIMIT %s
            """
            await cursor.execute(query, (user_id, limit))
            results = await cursor.fetchall()
            
            diaries = []
            for row in results:
                diary = DiaryListItemResponse(
                    idx=row["diary_id"],
                    user_title=row["user_title"],
                    user_content=row["user_content"],
                    plant_nickname=row.get("plant_nickname"),
                    plant_species=row.get("plant_species"),
                    plant_reply=row.get("plant_content"),
                    weather=row.get("weather"),
                    weather_icon=row.get("weather_icon"),
                    img_url=row.get("diary_img_url"),
                    hashtag=row.get("hashtag"),
                    created_at=row["created_at"],
                    updated_at=row.get("updated_at")
                )
                diaries.append(diary)
            
            return diaries
            
        except Exception as e:
            raise Exception(f"최근 일기 조회 중 오류: {str(e)}")