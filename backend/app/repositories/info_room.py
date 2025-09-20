import aiomysql
from typing import List, Optional
from datetime import datetime
from db.pool import get_db_connection
from schemas.info_room import (
    PlantWikiInfo,
    PestWikiInfo,
    PlantWikiListResponse,
    PestWikiListResponse,
    PlantWikiDetailResponse,
    PestWikiDetailResponse,
    InfoRoomStatsResponse,
    PlantInfoResponse,
    PlantInfoListResponse,
    PlantInfoSearchRequest
)

async def get_plant_wiki_list(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None
) -> PlantWikiListResponse:
    """식물 위키 목록을 조회합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        # 검색 조건 설정
        where_clause = ""
        params = []
        
        if search:
            where_clause = "WHERE name_jong LIKE %s"
            params.append(f"%{search}%")
        
        # 전체 개수 조회
        count_query = f"SELECT COUNT(*) as total FROM plant_wiki {where_clause}"
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(count_query, params)
            count_result = await cursor.fetchone()
            total_count = count_result['total']
            
            # 페이지네이션 계산
            offset = (page - 1) * limit
            
            # 식물 위키 목록 조회
            list_query = f"""
            SELECT 
                wiki_plant_id,
                name_jong,
                feature,
                temp,
                watering,
                flowering,
                flower_color,
                fertilizer,
                pruning,
                repot,
                toxic
            FROM plant_wiki 
            {where_clause}
            ORDER BY name_jong ASC
            LIMIT %s OFFSET %s
            """
            
            list_params = params + [limit, offset]
            await cursor.execute(list_query, list_params)
            results = await cursor.fetchall()
            
            plants = [PlantWikiInfo(**result) for result in results]
            
            return PlantWikiListResponse(
                plants=plants,
                total_count=total_count,
                page=page,
                limit=limit
            )
            
    except Exception as e:
        print(f"Error in get_plant_wiki_list: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_plant_wiki_detail(wiki_plant_id: int) -> Optional[PlantWikiDetailResponse]:
    """특정 식물 위키 상세 정보를 조회합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        query = """
        SELECT 
            wiki_plant_id,
            name_jong,
            feature,
            temp,
            watering,
            flowering,
            flower_color,
            fertilizer,
            pruning,
            repot,
            toxic
        FROM plant_wiki 
        WHERE wiki_plant_id = %s
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (wiki_plant_id,))
            result = await cursor.fetchone()
            
            if not result:
                return None
                
            return PlantWikiDetailResponse(**result)
            
    except Exception as e:
        print(f"Error in get_plant_wiki_detail: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_pest_wiki_list(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None
) -> PestWikiListResponse:
    """병충해 위키 목록을 조회합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        # 검색 조건 설정
        where_clause = ""
        params = []
        
        if search:
            where_clause = "WHERE pest_name LIKE %s"
            params.append(f"%{search}%")
        
        # 전체 개수 조회
        count_query = f"SELECT COUNT(*) as total FROM pest_wiki {where_clause}"
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(count_query, params)
            count_result = await cursor.fetchone()
            total_count = count_result['total']
            
            # 페이지네이션 계산
            offset = (page - 1) * limit
            
            # 병충해 위키 목록 조회
            list_query = f"""
            SELECT 
                pest_id,
                pest_name,
                cause,
                cure,
                prevention
            FROM pest_wiki 
            {where_clause}
            ORDER BY pest_name ASC
            LIMIT %s OFFSET %s
            """
            
            list_params = params + [limit, offset]
            await cursor.execute(list_query, list_params)
            results = await cursor.fetchall()
            
            pests = [PestWikiInfo(**result) for result in results]
            
            return PestWikiListResponse(
                pests=pests,
                total_count=total_count,
                page=page,
                limit=limit
            )
            
    except Exception as e:
        print(f"Error in get_pest_wiki_list: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_pest_wiki_detail(pest_id: int) -> Optional[PestWikiDetailResponse]:
    """특정 병충해 위키 상세 정보를 조회합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        query = """
        SELECT 
            pest_id,
            pest_name,
            cause,
            cure,
            prevention
        FROM pest_wiki 
        WHERE pest_id = %s
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (pest_id,))
            result = await cursor.fetchone()
            
            if not result:
                return None
                
            return PestWikiDetailResponse(**result)
            
    except Exception as e:
        print(f"Error in get_pest_wiki_detail: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_info_room_stats() -> InfoRoomStatsResponse:
    """정보방 통계 정보를 조회합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        query = """
        SELECT 
            (SELECT COUNT(*) FROM plant_wiki) as total_plants,
            (SELECT COUNT(*) FROM pest_wiki) as total_pests,
            (SELECT MAX(updated_at) FROM plant_wiki) as last_updated
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query)
            result = await cursor.fetchone()
            
            return InfoRoomStatsResponse(
                total_plants=result['total_plants'],
                total_pests=result['total_pests'],
                last_updated=result['last_updated']
            )
            
    except Exception as e:
        print(f"Error in get_info_room_stats: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def search_plant_wiki_by_category(
    category: str,
    page: int = 1,
    limit: int = 20
) -> PlantWikiListResponse:
    """카테고리별 식물 위키를 검색합니다."""
    connection = None
    try:
        connection = await get_db_connection()
        
        # 카테고리별 검색 조건 설정
        where_clause = ""
        params = []
        
        if category == "flowering":
            where_clause = "WHERE flowering IS NOT NULL AND flowering != ''"
        elif category == "indoor":
            where_clause = "WHERE temp LIKE '%실내%' OR temp LIKE '%18-25%'"
        elif category == "outdoor":
            where_clause = "WHERE temp LIKE '%야외%' OR temp LIKE '%15-30%'"
        elif category == "easy_care":
            where_clause = "WHERE watering LIKE '%적게%' OR watering LIKE '%일주일%'"
        
        # 전체 개수 조회
        count_query = f"SELECT COUNT(*) as total FROM plant_wiki {where_clause}"
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(count_query, params)
            count_result = await cursor.fetchone()
            total_count = count_result['total']
            
            # 페이지네이션 계산
            offset = (page - 1) * limit
            
            # 식물 위키 목록 조회
            list_query = f"""
            SELECT 
                wiki_plant_id,
                name_jong,
                feature,
                temp,
                watering,
                flowering,
                flower_color,
                fertilizer,
                pruning,
                repot,
                toxic
            FROM plant_wiki 
            {where_clause}
            ORDER BY name_jong ASC
            LIMIT %s OFFSET %s
            """
            
            list_params = params + [limit, offset]
            await cursor.execute(list_query, list_params)
            results = await cursor.fetchall()
            
            plants = [PlantWikiInfo(**result) for result in results]
            
            return PlantWikiListResponse(
                plants=plants,
                total_count=total_count,
                page=page,
                limit=limit
            )
            
    except Exception as e:
        print(f"Error in search_plant_wiki_by_category: {e}")
        raise e
    finally:
        if connection:
            connection.close()

# API에서 사용하는 함수들 (기존 위키 함수들을 래핑)
async def get_plant_info_list(
    page: int = 1,
    limit: int = 20,
    species: Optional[str] = None
) -> PlantInfoListResponse:
    """식물 정보 목록을 조회합니다."""
    wiki_response = await get_plant_wiki_list(page=page, limit=limit, search=species)
    
    # PlantWikiInfo를 PlantInfoResponse로 변환
    plants = [
        PlantInfoResponse(
            wiki_plant_id=plant.wiki_plant_id,
            name_jong=plant.name_jong,
            feature=plant.feature,
            temp=plant.temp,
            watering=plant.watering,
            flowering=plant.flowering,
            flower_color=plant.flower_color,
            fertilizer=plant.fertilizer,
            pruning=plant.pruning,
            repot=plant.repot,
            toxic=plant.toxic
        ) for plant in wiki_response.plants
    ]
    
    return PlantInfoListResponse(
        plants=plants,
        total_count=wiki_response.total_count,
        page=wiki_response.page,
        limit=wiki_response.limit
    )

async def get_plant_info_by_id(plant_id: int) -> Optional[PlantInfoResponse]:
    """특정 식물의 상세 정보를 조회합니다."""
    wiki_detail = await get_plant_wiki_detail(plant_id)
    
    if not wiki_detail:
        return None
    
    return PlantInfoResponse(
        wiki_plant_id=wiki_detail.wiki_plant_id,
        name_jong=wiki_detail.name_jong,
        feature=wiki_detail.feature,
        temp=wiki_detail.temp,
        watering=wiki_detail.watering,
        flowering=wiki_detail.flowering,
        flower_color=wiki_detail.flower_color,
        fertilizer=wiki_detail.fertilizer,
        pruning=wiki_detail.pruning,
        repot=wiki_detail.repot,
        toxic=wiki_detail.toxic
    )

async def search_plant_info(
    request: PlantInfoSearchRequest,
    page: int = 1,
    limit: int = 20
) -> PlantInfoListResponse:
    """식물 정보를 검색합니다."""
    wiki_response = await get_plant_wiki_list(page=page, limit=limit, search=request.query)
    
    # PlantWikiInfo를 PlantInfoResponse로 변환
    plants = [
        PlantInfoResponse(
            wiki_plant_id=plant.wiki_plant_id,
            name_jong=plant.name_jong,
            feature=plant.feature,
            temp=plant.temp,
            watering=plant.watering,
            flowering=plant.flowering,
            flower_color=plant.flower_color,
            fertilizer=plant.fertilizer,
            pruning=plant.pruning,
            repot=plant.repot,
            toxic=plant.toxic
        ) for plant in wiki_response.plants
    ]
    
    return PlantInfoListResponse(
        plants=plants,
        total_count=wiki_response.total_count,
        page=wiki_response.page,
        limit=wiki_response.limit
    )

async def get_plant_info_by_species(species: str) -> Optional[PlantInfoResponse]:
    """식물 종류로 식물 정보를 조회합니다."""
    wiki_response = await get_plant_wiki_list(page=1, limit=1, search=species)
    
    if not wiki_response.plants:
        return None
    
    plant = wiki_response.plants[0]
    return PlantInfoResponse(
        wiki_plant_id=plant.wiki_plant_id,
        name_jong=plant.name_jong,
        feature=plant.feature,
        temp=plant.temp,
        watering=plant.watering,
        flowering=plant.flowering,
        flower_color=plant.flower_color,
        fertilizer=plant.fertilizer,
        pruning=plant.pruning,
        repot=plant.repot,
        toxic=plant.toxic
    )
