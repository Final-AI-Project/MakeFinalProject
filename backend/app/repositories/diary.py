from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
import aiomysql
from db.pool import get_db_connection
from models.diary import Diary
from schemas.diary import DiaryCreate, DiaryUpdate, DiaryWriteRequest
from clients.plant_llm import get_plant_llm_response
from services.image_service import save_uploaded_image


async def create_diary(diary_request: DiaryWriteRequest, user_id: str, image_file=None, weather: str = None, weather_icon: str = None) -> Diary:
    """일기 생성"""
    async with get_db_connection() as (conn, cursor):
        try:
            # 이미지 저장 (있는 경우)
            img_url = None
            if image_file:
                img_url = await save_uploaded_image(image_file, "diaries")
            
            # LLM 답변 생성
            plant_reply = None
            if diary_request.plant_species and diary_request.user_content:
                try:
                    llm_response = await get_plant_llm_response(
                        plant_species=diary_request.plant_species,
                        user_content=diary_request.user_content,
                        plant_nickname=diary_request.plant_nickname
                    )
                    plant_reply = llm_response.get("reply", "")
                except Exception as e:
                    print(f"LLM 응답 생성 실패: {e}")
                    plant_reply = "식물이 답변을 준비 중입니다. 잠시 후 다시 확인해주세요."
            
            # 일기 데이터 삽입
            insert_query = """
                INSERT INTO diary (
                    user_id, user_title, user_content, hashtag, 
                    plant_id, plant_content, weather, 
                    hist_watered, hist_repot, hist_pruning, hist_fertilize, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # 해시태그에서 활동 기록 추출
            hashtag = diary_request.hashtag or ""
            hist_watered = 1 if "물주기" in hashtag or "물" in hashtag else 0
            hist_repot = 1 if "분갈이" in hashtag or "화분" in hashtag else 0
            hist_pruning = 1 if "가지치기" in hashtag or "전지" in hashtag else 0
            hist_fertilize = 1 if "비료" in hashtag or "영양제" in hashtag else 0
            
            # plant_id는 일단 0으로 설정 (나중에 실제 식물 ID로 연결)
            plant_id = 0
            
            await cursor.execute(insert_query, (
                user_id,
                diary_request.user_title,
                diary_request.user_content,
                hashtag,
                plant_id,
                plant_reply,
                weather,
                hist_watered,
                hist_repot,
                hist_pruning,
                hist_fertilize,
                datetime.now()
            ))
            
            diary_id = cursor.lastrowid
            
            # 이미지 URL을 img_address 테이블에 저장
            if img_url:
                img_insert_query = """
                    INSERT INTO img_address (diary_id, img_url, created_at)
                    VALUES (%s, %s, %s)
                """
                await cursor.execute(img_insert_query, (diary_id, img_url, datetime.now()))
            
            await conn.commit()
            
            # 생성된 일기 조회
            select_query = """
                SELECT d.*, ia.img_url as diary_img_url
                FROM diary d
                LEFT JOIN img_address ia ON d.diary_id = ia.diary_id
                WHERE d.diary_id = %s
            """
            await cursor.execute(select_query, (diary_id,))
            result = await cursor.fetchone()
            
            if result:
                return Diary.from_dict(dict(result))
            else:
                raise Exception("일기 생성 후 조회 실패")
                
        except Exception as e:
            await conn.rollback()
            raise Exception(f"일기 생성 중 오류: {str(e)}")


async def get_user_diaries(user_id: str, limit: int = 20, offset: int = 0) -> List[Diary]:
    """사용자의 일기 목록 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            query = """
                SELECT d.*, ia.img_url as diary_img_url
                FROM diary d
                LEFT JOIN img_address ia ON d.diary_id = ia.diary_id
                WHERE d.user_id = %s
                ORDER BY d.created_at DESC
                LIMIT %s OFFSET %s
            """
            await cursor.execute(query, (user_id, limit, offset))
            results = await cursor.fetchall()
            
            return [Diary.from_dict(dict(row)) for row in results]
            
        except Exception as e:
            raise Exception(f"일기 목록 조회 중 오류: {str(e)}")


async def get_diary_by_id(diary_id: int, user_id: str) -> Optional[Diary]:
    """특정 일기 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            query = """
                SELECT d.*, ia.img_url as diary_img_url
                FROM diary d
                LEFT JOIN img_address ia ON d.diary_id = ia.diary_id
                WHERE d.diary_id = %s AND d.user_id = %s
            """
            await cursor.execute(query, (diary_id, user_id))
            result = await cursor.fetchone()
            
            if result:
                return Diary.from_dict(dict(result))
            return None
            
        except Exception as e:
            raise Exception(f"일기 조회 중 오류: {str(e)}")


async def update_diary(diary_id: int, diary_request: DiaryUpdate, user_id: str, image_file=None) -> Optional[Diary]:
    """일기 수정"""
    async with get_db_connection() as (conn, cursor):
        try:
            # 기존 일기 조회
            existing_diary = await get_diary_by_id(diary_id, user_id)
            if not existing_diary:
                return None
            
            # 이미지 업데이트 (있는 경우)
            img_url = existing_diary.img_url
            if image_file:
                img_url = await save_uploaded_image(image_file, "diaries")
            
            # LLM 답변 재생성 (내용이 변경된 경우)
            plant_reply = existing_diary.plant_reply
            if diary_request.user_content and diary_request.user_content != existing_diary.user_content:
                try:
                    llm_response = await get_plant_llm_response(
                        plant_species=diary_request.plant_species or existing_diary.plant_species,
                        user_content=diary_request.user_content,
                        plant_nickname=diary_request.plant_nickname or existing_diary.plant_nickname
                    )
                    plant_reply = llm_response.get("reply", "")
                except Exception as e:
                    print(f"LLM 응답 재생성 실패: {e}")
            
            # 일기 업데이트
            update_fields = []
            update_values = []
            
            if diary_request.user_title is not None:
                update_fields.append("user_title = %s")
                update_values.append(diary_request.user_title)
            
            if diary_request.user_content is not None:
                update_fields.append("user_content = %s")
                update_values.append(diary_request.user_content)
            
            if diary_request.hashtag is not None:
                update_fields.append("hashtag = %s")
                update_values.append(diary_request.hashtag)
            
            if diary_request.weather is not None:
                update_fields.append("weather = %s")
                update_values.append(diary_request.weather)
            
            if diary_request.weather_icon is not None:
                update_fields.append("weather_icon = %s")
                update_values.append(diary_request.weather_icon)
            
            if plant_reply != existing_diary.plant_reply:
                update_fields.append("plant_content = %s")
                update_values.append(plant_reply)
            
            if update_fields:
                update_fields.append("updated_at = %s")
                update_values.append(datetime.now())
                update_values.append(diary_id)
                update_values.append(user_id)
                
                update_query = f"""
                    UPDATE diary 
                    SET {', '.join(update_fields)}
                    WHERE diary_id = %s AND user_id = %s
                """
                await cursor.execute(update_query, update_values)
            
            # 이미지 URL 업데이트
            if img_url != existing_diary.img_url:
                if img_url:
                    # 기존 이미지 삭제 후 새 이미지 추가
                    await cursor.execute("DELETE FROM img_address WHERE diary_id = %s", (diary_id,))
                    await cursor.execute(
                        "INSERT INTO img_address (diary_id, img_url, created_at) VALUES (%s, %s, %s)",
                        (diary_id, img_url, datetime.now())
                    )
                else:
                    await cursor.execute("DELETE FROM img_address WHERE diary_id = %s", (diary_id,))
            
            await conn.commit()
            
            # 업데이트된 일기 조회
            return await get_diary_by_id(diary_id, user_id)
            
        except Exception as e:
            await conn.rollback()
            raise Exception(f"일기 수정 중 오류: {str(e)}")


async def delete_diary(diary_id: int, user_id: str) -> bool:
    """일기 삭제"""
    async with get_db_connection() as (conn, cursor):
        try:
            # 관련 이미지 삭제
            await cursor.execute("DELETE FROM img_address WHERE diary_id = %s", (diary_id,))
            
            # 일기 삭제
            await cursor.execute("DELETE FROM diary WHERE diary_id = %s AND user_id = %s", (diary_id, user_id))
            
            if cursor.rowcount > 0:
                await conn.commit()
                return True
            return False
            
        except Exception as e:
            await conn.rollback()
            raise Exception(f"일기 삭제 중 오류: {str(e)}")


async def get_user_plants_for_diary(user_id: str) -> List[Dict[str, Any]]:
    """일기 작성용 사용자 식물 목록 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            query = """
                SELECT idx, plant_name, species
                FROM user_plant
                WHERE user_id = %s
                ORDER BY plant_name
            """
            await cursor.execute(query, (user_id,))
            results = await cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            raise Exception(f"식물 목록 조회 중 오류: {str(e)}")


async def get_diary_stats(user_id: str) -> Dict[str, Any]:
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
                SELECT plant_id, COUNT(*) as count
                FROM diary 
                WHERE user_id = %s AND plant_id > 0
                GROUP BY plant_id
                ORDER BY count DESC
                LIMIT 1
            """, (user_id,))
            most_active = await cursor.fetchone()
            
            return {
                "total_diaries": total_diaries,
                "recent_diaries": recent_diaries,
                "most_active_plant_id": most_active["plant_id"] if most_active else None,
                "most_active_count": most_active["count"] if most_active else 0
            }
            
        except Exception as e:
            raise Exception(f"일기 통계 조회 중 오류: {str(e)}")