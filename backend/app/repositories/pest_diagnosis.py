from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
import aiomysql
from db.pool import get_db_connection
from models.pest_wiki import PestWiki
from schemas.disease_diagnosis import DiseasePrediction, DiseaseDiagnosisResponse


async def get_user_pest_diagnosis_history(user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """사용자의 병충해 진단 기록 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            # 병충해 진단 기록이 저장되는 테이블이 없다면, 
            # 일단 pest_wiki 테이블에서 데이터를 가져오는 것으로 대체
            # 실제로는 별도의 진단 기록 테이블이 필요할 수 있음
            
            query = """
                SELECT 
                    pw.pest_id,
                    pw.pest_name,
                    pw.pathogen,
                    pw.symptom,
                    pw.cause,
                    pw.cure,
                    up.plant_name,
                    up.species,
                    '2024-01-15' as diagnosed_at,  -- 임시 날짜
                    0.85 as confidence,  -- 임시 신뢰도
                    '진단 기록' as notes
                FROM pest_wiki pw
                CROSS JOIN user_plant up
                WHERE up.user_id = %s
                ORDER BY pw.pest_id DESC
                LIMIT %s OFFSET %s
            """
            await cursor.execute(query, (user_id, limit, offset))
            results = await cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            raise Exception(f"병충해 진단 기록 조회 중 오류: {str(e)}")


async def get_pest_diagnosis_by_plant(user_id: str, plant_id: int) -> List[Dict[str, Any]]:
    """특정 식물의 병충해 진단 기록 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            query = """
                SELECT 
                    pw.pest_id,
                    pw.pest_name,
                    pw.pathogen,
                    pw.symptom,
                    pw.cause,
                    pw.cure,
                    up.plant_name,
                    up.species,
                    '2024-01-15' as diagnosed_at,  -- 임시 날짜
                    0.85 as confidence,  -- 임시 신뢰도
                    '진단 기록' as notes
                FROM pest_wiki pw
                JOIN user_plant up ON up.idx = %s
                WHERE up.user_id = %s
                ORDER BY pw.pest_id DESC
            """
            await cursor.execute(query, (plant_id, user_id))
            results = await cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            raise Exception(f"식물별 병충해 진단 기록 조회 중 오류: {str(e)}")


async def get_pest_wiki_by_id(pest_id: int) -> Optional[Dict[str, Any]]:
    """병충해 위키 정보 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            query = """
                SELECT pest_id, pest_name, pathogen, symptom, cause, cure
                FROM pest_wiki
                WHERE pest_id = %s
            """
            await cursor.execute(query, (pest_id,))
            result = await cursor.fetchone()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            raise Exception(f"병충해 위키 조회 중 오류: {str(e)}")


async def get_all_pest_wiki() -> List[Dict[str, Any]]:
    """모든 병충해 위키 정보 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            query = """
                SELECT pest_id, pest_name, pathogen, symptom, cause, cure
                FROM pest_wiki
                ORDER BY pest_name
            """
            await cursor.execute(query)
            results = await cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            raise Exception(f"병충해 위키 목록 조회 중 오류: {str(e)}")


async def save_pest_diagnosis_result(
    user_id: str, 
    plant_id: int, 
    predictions: List[DiseasePrediction],
    image_url: str,
    notes: str = ""
) -> int:
    """병충해 진단 결과 저장"""
    async with get_db_connection() as (conn, cursor):
        try:
            # 실제로는 별도의 진단 기록 테이블이 필요
            # 현재는 pest_wiki 테이블을 활용하여 임시 구현
            
            # 가장 높은 신뢰도의 예측 결과를 선택
            best_prediction = max(predictions, key=lambda x: x.confidence)
            
            # 진단 기록 저장 (임시로 pest_wiki 테이블 활용)
            # 실제로는 별도의 diagnosis_history 테이블이 필요
            insert_query = """
                INSERT INTO pest_wiki (
                    pest_name, pathogen, symptom, cause, cure
                ) VALUES (%s, %s, %s, %s, %s)
            """
            
            await cursor.execute(insert_query, (
                best_prediction.disease_name,
                best_prediction.description,
                best_prediction.description,
                best_prediction.description,
                best_prediction.treatment
            ))
            
            diagnosis_id = cursor.lastrowid
            await conn.commit()
            
            return diagnosis_id
            
        except Exception as e:
            await conn.rollback()
            raise Exception(f"병충해 진단 결과 저장 중 오류: {str(e)}")


async def get_user_plants_with_pest_history(user_id: str) -> List[Dict[str, Any]]:
    """병충해 진단 기록이 있는 사용자 식물 목록 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            query = """
                SELECT DISTINCT
                    up.idx as plant_id,
                    up.plant_name,
                    up.species,
                    COUNT(pw.pest_id) as diagnosis_count,
                    MAX('2024-01-15') as last_diagnosis_date  -- 임시 날짜
                FROM user_plant up
                LEFT JOIN pest_wiki pw ON 1=1  -- 임시 조인
                WHERE up.user_id = %s
                GROUP BY up.idx, up.plant_name, up.species
                HAVING diagnosis_count > 0
                ORDER BY last_diagnosis_date DESC
            """
            await cursor.execute(query, (user_id,))
            results = await cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            raise Exception(f"병충해 진단 기록이 있는 식물 목록 조회 중 오류: {str(e)}")


async def get_recent_pest_diagnoses(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """최근 병충해 진단 기록 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            query = """
                SELECT 
                    pw.pest_id,
                    pw.pest_name,
                    pw.symptom,
                    up.plant_name,
                    up.species,
                    '2024-01-15' as diagnosed_at,  -- 임시 날짜
                    0.85 as confidence  -- 임시 신뢰도
                FROM pest_wiki pw
                CROSS JOIN user_plant up
                WHERE up.user_id = %s
                ORDER BY pw.pest_id DESC
                LIMIT %s
            """
            await cursor.execute(query, (user_id, limit))
            results = await cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            raise Exception(f"최근 병충해 진단 기록 조회 중 오류: {str(e)}")


async def get_pest_diagnosis_statistics(user_id: str) -> Dict[str, Any]:
    """병충해 진단 통계 조회"""
    async with get_db_connection() as (conn, cursor):
        try:
            # 전체 진단 수
            await cursor.execute("SELECT COUNT(*) as total FROM pest_wiki")
            total_diagnoses = (await cursor.fetchone())["total"]
            
            # 사용자 식물 수
            await cursor.execute("SELECT COUNT(*) as plant_count FROM user_plant WHERE user_id = %s", (user_id,))
            plant_count = (await cursor.fetchone())["plant_count"]
            
            # 최근 7일 진단 수 (임시)
            recent_diagnoses = min(5, total_diagnoses)  # 임시 값
            
            return {
                "total_diagnoses": total_diagnoses,
                "plant_count": plant_count,
                "recent_diagnoses": recent_diagnoses,
                "most_common_pest": "진균병",  # 임시 값
                "diagnosis_trend": "증가"  # 임시 값
            }
            
        except Exception as e:
            raise Exception(f"병충해 진단 통계 조회 중 오류: {str(e)}")
