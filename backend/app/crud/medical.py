import aiomysql
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from models.medical import MedicalDiagnosis


async def get_user_medical_diagnoses(
    db: tuple[aiomysql.Connection, aiomysql.DictCursor],
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[MedicalDiagnosis]:
    """사용자의 모든 병충해 진단 기록을 조회합니다. (기존 테이블 기반)"""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            """
            SELECT 
                upp.idx,
                upp.plant_id,
                upp.pest_id,
                upp.pest_date,
                up.plant_name,
                pw.pest_name,
                pw.cause,
                pw.cure,
                up.species as plant_species,
                up.meet_day
            FROM user_plant_pest upp
            JOIN user_plant up ON upp.plant_id = up.plant_id
            JOIN pest_wiki pw ON upp.pest_id = pw.pest_id
            WHERE up.user_id = %s
            ORDER BY upp.pest_date DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, limit, offset)
        )
        results = await cursor.fetchall()
        return [MedicalDiagnosis.from_dict(result) for result in results]


async def get_medical_diagnosis_by_id(
    db: tuple[aiomysql.Connection, aiomysql.DictCursor],
    diagnosis_id: int,
    user_id: str
) -> Optional[MedicalDiagnosis]:
    """특정 병충해 진단 기록을 조회합니다."""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            """
            SELECT 
                upp.idx,
                upp.plant_id,
                upp.pest_id,
                upp.pest_date,
                up.plant_name,
                pw.pest_name,
                pw.cause,
                pw.cure,
                up.species as plant_species,
                up.meet_day
            FROM user_plant_pest upp
            JOIN user_plant up ON upp.plant_id = up.plant_id
            JOIN pest_wiki pw ON upp.pest_id = pw.pest_id
            WHERE upp.idx = %s AND up.user_id = %s
            """,
            (diagnosis_id, user_id)
        )
        result = await cursor.fetchone()
        return MedicalDiagnosis.from_dict(result) if result else None


async def create_medical_diagnosis(
    db: tuple[aiomysql.Connection, aiomysql.DictCursor],
    *,
    plant_id: int,
    pest_id: int,
    pest_date: date,
) -> MedicalDiagnosis:
    """새로운 병충해 진단 기록을 생성합니다."""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            """
            INSERT INTO user_plant_pest (plant_id, pest_id, pest_date)
            VALUES (%s, %s, %s)
            """,
            (plant_id, pest_id, pest_date)
        )
        diagnosis_id = cursor.lastrowid
        
        # 생성된 진단 기록 조회
        await cursor.execute(
            """
            SELECT 
                upp.idx,
                upp.plant_id,
                upp.pest_id,
                upp.pest_date,
                up.plant_name,
                pw.pest_name,
                pw.cause,
                pw.cure,
                up.species as plant_species,
                up.meet_day
            FROM user_plant_pest upp
            JOIN user_plant up ON upp.plant_id = up.plant_id
            JOIN pest_wiki pw ON upp.pest_id = pw.pest_id
            WHERE upp.idx = %s
            """,
            (diagnosis_id,)
        )
        result = await cursor.fetchone()
        return MedicalDiagnosis.from_dict(result)


async def update_medical_diagnosis(
    db: tuple[aiomysql.Connection, aiomysql.DictCursor],
    diagnosis_id: int,
    user_id: str,
    *,
    pest_id: Optional[int] = None,
    pest_date: Optional[date] = None,
) -> Optional[MedicalDiagnosis]:
    """병충해 진단 기록을 수정합니다."""
    # 업데이트할 필드들 동적 생성
    update_fields = []
    update_values = []
    
    if pest_id is not None:
        update_fields.append("pest_id = %s")
        update_values.append(pest_id)
    if pest_date is not None:
        update_fields.append("pest_date = %s")
        update_values.append(pest_date)
    
    if not update_fields:
        return None
    
    update_values.extend([diagnosis_id, user_id])
    
    async with db.cursor(aiomysql.DictCursor) as cursor:
        # 먼저 해당 진단이 사용자의 식물인지 확인
        await cursor.execute(
            """
            SELECT upp.idx FROM user_plant_pest upp
            JOIN user_plant up ON upp.plant_id = up.plant_id
            WHERE upp.idx = %s AND up.user_id = %s
            """,
            (diagnosis_id, user_id)
        )
        if not await cursor.fetchone():
            return None
        
        await cursor.execute(
            f"""
            UPDATE user_plant_pest 
            SET {', '.join(update_fields)}
            WHERE idx = %s
            """,
            update_values
        )
        
        if cursor.rowcount == 0:
            return None
        
        # 수정된 진단 기록 조회
        await cursor.execute(
            """
            SELECT 
                upp.idx,
                upp.plant_id,
                upp.pest_id,
                upp.pest_date,
                up.plant_name,
                pw.pest_name,
                pw.cause,
                pw.cure,
                up.species as plant_species,
                up.meet_day
            FROM user_plant_pest upp
            JOIN user_plant up ON upp.plant_id = up.plant_id
            JOIN pest_wiki pw ON upp.pest_id = pw.pest_id
            WHERE upp.idx = %s
            """,
            (diagnosis_id,)
        )
        result = await cursor.fetchone()
        return MedicalDiagnosis.from_dict(result) if result else None


async def delete_medical_diagnosis(
    db: tuple[aiomysql.Connection, aiomysql.DictCursor],
    diagnosis_id: int,
    user_id: str
) -> bool:
    """병충해 진단 기록을 삭제합니다."""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            """
            DELETE upp FROM user_plant_pest upp
            JOIN user_plant up ON upp.plant_id = up.plant_id
            WHERE upp.idx = %s AND up.user_id = %s
            """,
            (diagnosis_id, user_id)
        )
        return cursor.rowcount > 0


async def get_medical_stats(
    db: tuple[aiomysql.Connection, aiomysql.DictCursor],
    user_id: str
) -> Dict[str, Any]:
    """사용자의 병충해 진단 통계를 조회합니다."""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        # 총 진단 수
        await cursor.execute(
            """
            SELECT COUNT(*) as total 
            FROM user_plant_pest upp
            JOIN user_plant up ON upp.plant_id = up.plant_id
            WHERE up.user_id = %s
            """,
            (user_id,)
        )
        total_result = await cursor.fetchone()
        total_diagnoses = total_result['total'] if total_result else 0
        
        # 진단받은 식물 수
        await cursor.execute(
            """
            SELECT COUNT(DISTINCT upp.plant_id) as active_plants 
            FROM user_plant_pest upp
            JOIN user_plant up ON upp.plant_id = up.plant_id
            WHERE up.user_id = %s
            """,
            (user_id,)
        )
        plants_result = await cursor.fetchone()
        active_plants = plants_result['active_plants'] if plants_result else 0
        
        # 가장 흔한 병충해
        await cursor.execute(
            """
            SELECT pw.pest_name, COUNT(*) as count 
            FROM user_plant_pest upp
            JOIN user_plant up ON upp.plant_id = up.plant_id
            JOIN pest_wiki pw ON upp.pest_id = pw.pest_id
            WHERE up.user_id = %s 
            GROUP BY pw.pest_name 
            ORDER BY count DESC 
            LIMIT 1
            """,
            (user_id,)
        )
        common_pest_result = await cursor.fetchone()
        most_common_pest = common_pest_result['pest_name'] if common_pest_result else None
        
        # 최근 7일 진단 수
        await cursor.execute(
            """
            SELECT COUNT(*) as recent 
            FROM user_plant_pest upp
            JOIN user_plant up ON upp.plant_id = up.plant_id
            WHERE up.user_id = %s AND upp.pest_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """,
            (user_id,)
        )
        recent_result = await cursor.fetchone()
        recent_diagnoses = recent_result['recent'] if recent_result else 0
        
        return {
            'total_diagnoses': total_diagnoses,
            'active_plants': active_plants,
            'most_common_pest': most_common_pest,
            'recent_diagnoses': recent_diagnoses
        }


async def get_related_diagnoses(
    db: tuple[aiomysql.Connection, aiomysql.DictCursor],
    plant_id: int,
    user_id: str,
    exclude_id: Optional[int] = None,
    limit: int = 5
) -> List[MedicalDiagnosis]:
    """같은 식물의 관련 진단 기록을 조회합니다."""
    async with db.cursor(aiomysql.DictCursor) as cursor:
        query = """
            SELECT 
                upp.idx,
                upp.plant_id,
                upp.pest_id,
                upp.pest_date,
                up.plant_name,
                pw.pest_name,
                pw.cause,
                pw.cure,
                up.species as plant_species,
                up.meet_day
            FROM user_plant_pest upp
            JOIN user_plant up ON upp.plant_id = up.plant_id
            JOIN pest_wiki pw ON upp.pest_id = pw.pest_id
            WHERE upp.plant_id = %s AND up.user_id = %s
        """
        params = [plant_id, user_id]
        
        if exclude_id:
            query += " AND upp.idx != %s"
            params.append(exclude_id)
        
        query += " ORDER BY upp.pest_date DESC LIMIT %s"
        params.append(limit)
        
        await cursor.execute(query, params)
        results = await cursor.fetchall()
        return [MedicalDiagnosis.from_dict(result) for result in results]
