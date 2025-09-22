from typing import Optional, Dict, Any
from db.pool import get_db_connection


async def get_plant_wiki_by_species(species_name: str) -> Optional[Dict[str, Any]]:
    """
    품종명으로 식물 위키 정보를 조회합니다.
    
    Args:
        species_name: 품종명 (한글 또는 영어)
        
    Returns:
        Dict[str, Any]: 위키 정보 또는 None
    """
    try:
        async with get_db_connection() as (conn, cursor):
            # 실제 테이블 구조에 맞게 조회 (sci_name, name_jong 등으로 검색)
            await cursor.execute(
                """
                SELECT 
                    wiki_plant_id,
                    sci_name,
                    name_jong,
                    name_sok,
                    name_gwa,
                    name_mok,
                    name_gang,
                    name_mun,
                    feature,
                    temp,
                    watering,
                    flowering,
                    flower_color,
                    flower_diam,
                    fertilizer,
                    pruning,
                    repot,
                    toxic
                FROM plant_wiki 
                WHERE sci_name LIKE %s 
                   OR name_jong LIKE %s 
                   OR name_sok LIKE %s
                LIMIT 1
                """,
                (f"%{species_name}%", f"%{species_name}%", f"%{species_name}%")
            )
            
            result = await cursor.fetchone()
            
            if result:
                return {
                    "wiki_plant_id": result["wiki_plant_id"],
                    "plant_name": result["name_jong"] or result["sci_name"],
                    "species": result["sci_name"],
                    "description": result["feature"],
                    "care_tips": f"온도: {result['temp'] or '정보없음'}, 개화: {result['flowering'] or '정보없음'}",
                    "watering_frequency": result["watering"],
                    "light_requirement": "정보없음",
                    "temperature_range": result["temp"],
                    "humidity_requirement": "정보없음",
                    "soil_type": "정보없음",
                    "fertilizer_frequency": result["fertilizer"],
                    "repotting_frequency": result["repot"],
                    "common_problems": "정보없음",
                    "toxicity_info": result["toxic"]
                }
            
            return None
            
    except Exception as e:
        print(f"[ERROR] plant_wiki 조회 오류: {e}")
        return None
