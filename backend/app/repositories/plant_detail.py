import aiomysql
from typing import List, Optional
from datetime import datetime
from db.pool import get_db_connection
from schemas.plant_detail import (
    PlantDetailResponse, 
    PlantDiaryResponse, 
    PlantPestRecordResponse,
    PlantDetailSummaryResponse,
    WateringRecordResponse,
    WateringRecordRequest,
    HealthStatusResponse,
    HealthAnalysisRequest,
    WateringSettingsRequest,
    WateringSettingsResponse,
    PlantSpeciesInfoResponse,
    PlantPestRecordRequest,
    PlantPestRecordAddResponse
)

async def get_plant_detail(plant_idx: int, user_id: str) -> PlantDetailResponse:
    """
    특정 식물의 상세 정보를 조회합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        query = """
        SELECT 
            up.idx,
            up.user_id,
            up.plant_id,
            up.plant_name,
            up.location,
            up.species,
            up.meet_day,
            up.on,
            
            -- 최신 습도 정보
            hi.humidity as current_humidity,
            hi.humid_date as humidity_date,
            
            -- 식물 위키 정보 (새로운 기본키 사용)
            pw.feature,
            pw.temp,
            pw.watering,
            pw.flowering,
            pw.flower_color,
            pw.fertilizer,
            pw.pruning,
            pw.repot,
            pw.toxic,
            
            -- 사용자 식물 사진 (img_address 테이블에서)
            ia.img_url as user_plant_image
            
        FROM user_plant up
        LEFT JOIN (
            SELECT 
                plant_id,
                humidity,
                humid_date,
                ROW_NUMBER() OVER (PARTITION BY plant_id ORDER BY humid_date DESC) as rn
            FROM humid_info
        ) hi ON up.plant_id = hi.plant_id AND hi.rn = 1
        LEFT JOIN plant_wiki pw ON up.plant_id = pw.wiki_plant_id
        LEFT JOIN (
            SELECT 
                ia.plant_id,
                ia.img_url,
                ROW_NUMBER() OVER (PARTITION BY ia.plant_id ORDER BY ia.idx DESC) as rn
            FROM img_address ia
            WHERE ia.img_url IS NOT NULL AND ia.img_url != ''
        ) ia ON up.plant_id = ia.plant_id AND ia.rn = 1
        WHERE up.idx = %s AND up.user_id = %s
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (plant_idx, user_id))
            result = await cursor.fetchone()
            
            if not result:
                raise ValueError("식물 정보를 찾을 수 없습니다.")
            
            # 일기 개수 조회
            diary_count = await get_plant_diary_count(plant_idx, user_id)
            
            return PlantDetailResponse(
                idx=result['idx'],
                user_id=result['user_id'],
                plant_id=result['plant_id'],
                plant_name=result['plant_name'],
                species=result['species'],
                meet_day=result['meet_day'],
                pest_id=None,  # user_plant 테이블에서 pest_id 제거됨
                on=result['on'],
                current_humidity=result['current_humidity'],
                humidity_date=result['humidity_date'],
                wiki_img=None,  # plant_wiki 테이블에 wiki_img 컬럼 없음
                feature=result['feature'],
                temp=result['temp'],
                watering=result['watering'],
                flowering=result['flowering'],
                flower_color=result['flower_color'],
                fertilizer=result['fertilizer'],
                pruning=result['pruning'],
                repot=result['repot'],
                toxic=result['toxic'],
                pest_cause=None,  # 별도 테이블에서 조회 필요
                pest_cure=None,  # 별도 테이블에서 조회 필요
                user_plant_image=result['user_plant_image'],
                diary_count=diary_count,
                growing_location=result['location']  # location 컬럼 추가
            )
            
    except Exception as e:
        print(f"Error in get_plant_detail: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_plant_diary_count(plant_idx: int, user_id: str) -> int:
    """
    특정 식물의 일기 개수를 조회합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        query = """
        SELECT COUNT(*) as count
        FROM diary d
        JOIN user_plant up ON d.user_id = up.user_id
        WHERE up.idx = %s AND up.user_id = %s
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (plant_idx, user_id))
            result = await cursor.fetchone()
            return result['count'] if result else 0
            
    except Exception as e:
        print(f"Error in get_plant_diary_count: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_plant_diaries(plant_idx: int, user_id: str, limit: int = 10) -> List[PlantDiaryResponse]:
    """
    특정 식물의 일기 목록을 조회합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        query = """
        SELECT 
            d.diary_id,
            d.user_id,
            d.user_title,
            d.img_url,
            d.user_content,
            d.hashtag,
            d.plant_content,
            d.weather,
            d.created_at
        FROM diary d
        JOIN user_plant up ON d.user_id = up.user_id
        WHERE up.idx = %s AND up.user_id = %s
        ORDER BY d.created_at DESC
        LIMIT %s
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (plant_idx, user_id, limit))
            results = await cursor.fetchall()
            
            diaries = []
            for row in results:
                diary = PlantDiaryResponse(
                    diary_id=row['diary_id'],
                    user_id=row['user_id'],
                    user_title=row['user_title'],
                    img_url=row['img_url'],
                    user_content=row['user_content'],
                    hashtag=row['hashtag'],
                    plant_content=row['plant_content'],
                    weather=row['weather'],
                    created_at=row['created_at']
                )
                diaries.append(diary)
            
            return diaries
            
    except Exception as e:
        print(f"Error in get_plant_diaries: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_plant_pest_records(plant_idx: int, user_id: str) -> List[PlantPestRecordResponse]:
    """
    특정 식물의 병해충 기록을 조회합니다.
    새로운 user_plant_pest 테이블을 사용합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        query = """
        SELECT 
            pw.pest_id,
            pw.pest_name,
            pw.cause,
            pw.cure,
            upp.idx as record_id,
            upp.pest_date as recorded_date
        FROM user_plant up
        JOIN user_plant_pest upp ON up.plant_id = upp.plant_id
        JOIN pest_wiki pw ON upp.pest_id = pw.pest_id
        WHERE up.idx = %s AND up.user_id = %s
        ORDER BY upp.pest_date DESC
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (plant_idx, user_id))
            results = await cursor.fetchall()
            
            pest_records = []
            for row in results:
                pest_record = PlantPestRecordResponse(
                    pest_id=row['pest_id'],
                    cause=row['cause'],
                    cure=row['cure'],
                    recorded_date=row['recorded_date']  # 현재 날짜 사용
                )
                pest_records.append(pest_record)
            
            return pest_records
            
    except Exception as e:
        print(f"Error in get_plant_pest_records: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_plant_humidity_history(plant_idx: int, user_id: str, limit: int = 7) -> List[dict]:
    """
    특정 식물의 습도 기록을 조회합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        query = """
        SELECT 
            hi.humidity,
            hi.humid_date
        FROM humid_info hi
        JOIN user_plant up ON hi.plant_id = up.plant_id
        WHERE up.idx = %s AND up.user_id = %s
        ORDER BY hi.humid_date DESC
        LIMIT %s
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (plant_idx, user_id, limit))
            results = await cursor.fetchall()
            return results
            
    except Exception as e:
        print(f"Error in get_plant_humidity_history: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def update_plant_info(plant_idx: int, user_id: str, update_data: dict) -> bool:
    """
    식물 정보를 수정합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        # 업데이트할 필드들만 동적으로 구성
        set_clauses = []
        values = []
        
        if 'plant_name' in update_data:
            set_clauses.append("plant_name = %s")
            values.append(update_data['plant_name'])
        
        if 'species' in update_data:
            set_clauses.append("species = %s")
            values.append(update_data['species'])
        
        if 'meet_day' in update_data:
            set_clauses.append("meet_day = %s")
            values.append(update_data['meet_day'])
        
        if not set_clauses:
            return False
        
        values.extend([plant_idx, user_id])
        
        query = f"""
        UPDATE user_plant 
        SET {', '.join(set_clauses)}
        WHERE idx = %s AND user_id = %s
        """
        
        async with connection.cursor() as cursor:
            result = await cursor.execute(query, values)
            await connection.commit()
            return result > 0
            
    except Exception as e:
        print(f"Error in update_plant_info: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def delete_plant(plant_idx: int, user_id: str) -> bool:
    """
    식물을 삭제합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        query = """
        DELETE FROM user_plant 
        WHERE idx = %s AND user_id = %s
        """
        
        async with connection.cursor() as cursor:
            result = await cursor.execute(query, (plant_idx, user_id))
            await connection.commit()
            return result > 0
            
    except Exception as e:
        print(f"Error in delete_plant: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_plant_detail_summary(plant_idx: int, user_id: str) -> PlantDetailSummaryResponse:
    """
    식물의 상세 요약 정보를 조회합니다.
    """
    try:
        # 기본 식물 정보
        plant_info = await get_plant_detail(plant_idx, user_id)
        
        # 최근 일기 목록
        recent_diaries = await get_plant_diaries(plant_idx, user_id, limit=5)
        
        # 병해충 기록
        pest_records = await get_plant_pest_records(plant_idx, user_id)
        
        # 습도 기록
        humidity_history = await get_plant_humidity_history(plant_idx, user_id, limit=7)
        
        # 습도 트렌드 계산
        humidity_trend = "stable"
        if len(humidity_history) >= 2:
            recent_humidity = humidity_history[0]['humidity']
            previous_humidity = humidity_history[1]['humidity']
            if recent_humidity > previous_humidity:
                humidity_trend = "increasing"
            elif recent_humidity < previous_humidity:
                humidity_trend = "decreasing"
        
        # 관리 알림 생성
        care_reminders = []
        if plant_info.current_humidity and plant_info.current_humidity < 30:
            care_reminders.append("습도가 낮습니다. 물을 주세요.")
        if pest_records:
            care_reminders.append("병해충이 발견되었습니다. 치료가 필요합니다.")
        if plant_info.diary_count == 0:
            care_reminders.append("첫 번째 일기를 작성해보세요!")
        
        return PlantDetailSummaryResponse(
            plant_info=plant_info,
            recent_diaries=recent_diaries,
            pest_records=pest_records,
            humidity_trend=humidity_trend,
            care_reminders=care_reminders
        )
        
    except Exception as e:
        print(f"Error in get_plant_detail_summary: {e}")
        raise e

async def check_humidity_increase_and_record_watering(plant_idx: int, user_id: str) -> dict:
    """
    습도 증가를 확인하고 10% 이상 증가 시 자동으로 물주기 기록을 생성합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        # 최근 2개의 습도 기록 조회
        query = """
        SELECT 
            hi.humidity,
            hi.humid_date
        FROM humid_info hi
        JOIN user_plant up ON hi.plant_id = up.plant_id
        WHERE up.idx = %s AND up.user_id = %s
        ORDER BY hi.humid_date DESC
        LIMIT 2
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (plant_idx, user_id))
            results = await cursor.fetchall()
            
            if len(results) < 2:
                return {
                    "status": "insufficient_data",
                    "message": "습도 데이터가 부족합니다. 최소 2개의 기록이 필요합니다.",
                    "watering_recorded": False
                }
            
            current_humidity = results[0]['humidity']
            previous_humidity = results[1]['humidity']
            
            # 습도 증가율 계산
            humidity_increase = ((current_humidity - previous_humidity) / previous_humidity) * 100 if previous_humidity != 0 else 0
            
            # 10% 이상 증가 시 물주기 기록 생성
            if humidity_increase >= 10:
                # 물주기 기록을 diary 테이블에 자동 생성
                watering_query = """
                INSERT INTO diary (user_id, user_title, user_content, hashtag, plant_content, weather, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                watering_title = "자동 감지된 물주기"
                watering_content = f"습도가 {humidity_increase:.1f}% 증가하여 물을 준 것으로 자동 기록되었습니다."
                watering_hashtag = "#물주기 #자동감지"
                plant_content = f"이전 습도: {previous_humidity:.1f}% → 현재 습도: {current_humidity:.1f}%"
                
                await cursor.execute(watering_query, (
                    user_id,
                    watering_title,
                    watering_content,
                    watering_hashtag,
                    plant_content,
                    "자동",
                    datetime.now()
                ))
                await connection.commit()
                
                return {
                    "status": "watering_recorded",
                    "message": f"습도가 {humidity_increase:.1f}% 증가하여 물주기가 자동 기록되었습니다.",
                    "watering_recorded": True,
                    "humidity_increase": humidity_increase,
                    "current_humidity": current_humidity,
                    "previous_humidity": previous_humidity
                }
            else:
                return {
                    "status": "no_watering_needed",
                    "message": f"습도 증가율이 {humidity_increase:.1f}%로 물주기 기록 기준(10%)에 미달합니다.",
                    "watering_recorded": False,
                    "humidity_increase": humidity_increase,
                    "current_humidity": current_humidity,
                    "previous_humidity": previous_humidity
                }
                
    except Exception as e:
        print(f"Error in check_humidity_increase_and_record_watering: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_watering_records(plant_idx: int, user_id: str, limit: int = 10) -> List[WateringRecordResponse]:
    """
    특정 식물의 물주기 기록을 조회합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        # 물주기 관련 일기 조회 (hashtag에 #물주기가 포함된 것들)
        query = """
        SELECT 
            d.diary_id,
            d.user_id,
            d.user_title,
            d.user_content,
            d.hashtag,
            d.plant_content,
            d.weather,
            d.created_at
        FROM diary d
        JOIN user_plant up ON d.user_id = up.user_id
        WHERE up.idx = %s AND up.user_id = %s 
        AND (d.hashtag LIKE '%물주기%' OR d.user_title LIKE '%물주기%')
        ORDER BY d.created_at DESC
        LIMIT %s
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (plant_idx, user_id, limit))
            results = await cursor.fetchall()
            
            watering_records = []
            for row in results:
                # 습도 정보 추출 (plant_content에서)
                humidity_before = None
                humidity_after = None
                humidity_increase = None
                
                if row['plant_content']:
                    import re
                    humidity_match = re.search(r'이전 습도: ([\d.]+)% → 현재 습도: ([\d.]+)%', row['plant_content'])
                    if humidity_match:
                        humidity_before = float(humidity_match.group(1))
                        humidity_after = float(humidity_match.group(2))
                        humidity_increase = humidity_after - humidity_before
                
                watering_record = WateringRecordResponse(
                    record_id=row['diary_id'],
                    plant_idx=plant_idx,
                    user_id=row['user_id'],
                    watering_date=row['created_at'],
                    humidity_before=humidity_before,
                    humidity_after=humidity_after,
                    humidity_increase=humidity_increase,
                    is_auto_detected="자동" in row['user_title'],
                    notes=row['user_content']
                )
                watering_records.append(watering_record)
            
            return watering_records
            
    except Exception as e:
        print(f"Error in get_watering_records: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def analyze_plant_health(plant_idx: int, user_id: str, leaf_health_score: Optional[float] = None) -> HealthStatusResponse:
    """
    식물의 종합적인 건강상태를 분석합니다.
    습도, 병해충, 잎 건강상태를 종합하여 "건강", "주의", "아픔"으로 판단합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        # 기본 식물 정보 조회
        plant_info = await get_plant_detail(plant_idx, user_id)
        
        # 습도 상태 분석
        humidity_status = "good"
        humidity_score = 100
        
        if plant_info.current_humidity is not None:
            if plant_info.current_humidity < 30:
                humidity_status = "low"
                humidity_score = 30
            elif plant_info.current_humidity > 80:
                humidity_status = "high"
                humidity_score = 40
            elif plant_info.current_humidity < 50:
                humidity_score = 70
            else:
                humidity_score = 100
        
        # 병해충 상태 분석 (새로운 테이블 구조에 맞게 수정)
        pest_status = "healthy"
        pest_score = 100
        
        # user_plant_pest 테이블에서 병충해 기록 확인
        pest_records = await get_plant_pest_records(plant_idx, user_id)
        if pest_records:
            pest_status = "infected"
            pest_score = 20
        else:
            pest_score = 100
        
        # 잎 건강상태 분석 (AI 모델 결과 또는 기본값)
        leaf_health_status = "healthy"
        leaf_score = 100
        
        if leaf_health_score is not None:
            if leaf_health_score >= 0.8:
                leaf_health_status = "healthy"
                leaf_score = 100
            elif leaf_health_score >= 0.5:
                leaf_health_status = "warning"
                leaf_score = 60
            else:
                leaf_health_status = "sick"
                leaf_score = 20
        else:
            # AI 모델 결과가 없으면 기본값 사용
            leaf_score = 80  # 중간값
        
        # 종합 건강 점수 계산 (가중평균)
        overall_score = int((humidity_score * 0.3 + pest_score * 0.4 + leaf_score * 0.3))
        
        # 전체 상태 판단
        if overall_score >= 80:
            overall_status = "건강"
        elif overall_score >= 50:
            overall_status = "주의"
        else:
            overall_status = "아픔"
        
        # 권장사항 생성
        recommendations = []
        urgent_actions = []
        
        if humidity_status == "low":
            recommendations.append("습도가 낮습니다. 물을 주세요.")
            urgent_actions.append("즉시 물주기 필요")
        elif humidity_status == "high":
            recommendations.append("습도가 높습니다. 통풍을 시켜주세요.")
        
        if pest_status == "infected":
            recommendations.append("병해충이 발견되었습니다. 치료가 필요합니다.")
            urgent_actions.append("병해충 치료 필요")
        
        if leaf_health_status == "warning":
            recommendations.append("잎 상태에 주의가 필요합니다.")
        elif leaf_health_status == "sick":
            recommendations.append("잎이 아픈 상태입니다. 전문가 상담을 권합니다.")
            urgent_actions.append("잎 건강 관리 필요")
        
        # 상세 상태 정보
        status_details = {
            "humidity": {
                "value": plant_info.current_humidity,
                "status": humidity_status,
                "score": humidity_score
            },
            "pest": {
                "has_pest": len(pest_records) > 0,
                "status": pest_status,
                "score": pest_score
            },
            "leaf_health": {
                "ai_score": leaf_health_score,
                "status": leaf_health_status,
                "score": leaf_score
            }
        }
        
        return HealthStatusResponse(
            plant_idx=plant_idx,
            user_id=user_id,
            overall_status=overall_status,
            health_score=overall_score,
            status_details=status_details,
            humidity_status=humidity_status,
            pest_status=pest_status,
            leaf_health_status=leaf_health_status,
            recommendations=recommendations,
            urgent_actions=urgent_actions
        )
        
    except Exception as e:
        print(f"Error in analyze_plant_health: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def record_manual_watering(plant_idx: int, user_id: str, watering_request: WateringRecordRequest) -> WateringRecordResponse:
    """
    수동으로 물주기 기록을 생성합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        # 현재 습도 조회
        current_humidity = None
        if plant_info := await get_plant_detail(plant_idx, user_id):
            current_humidity = plant_info.current_humidity
        
        # 물주기 일기 생성
        watering_query = """
        INSERT INTO diary (user_id, user_title, user_content, hashtag, plant_content, weather, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        watering_title = "물주기 기록"
        watering_content = watering_request.notes or "물을 주었습니다."
        watering_hashtag = "#물주기 #수동기록"
        plant_content = f"현재 습도: {current_humidity:.1f}%" if current_humidity else "습도 정보 없음"
        watering_date = watering_request.watering_date or datetime.now()
        
        async with connection.cursor() as cursor:
            result = await cursor.execute(watering_query, (
                user_id,
                watering_title,
                watering_content,
                watering_hashtag,
                plant_content,
                "수동",
                watering_date
            ))
            await connection.commit()
            
            record_id = cursor.lastrowid
            
            return WateringRecordResponse(
                record_id=record_id,
                plant_idx=plant_idx,
                user_id=user_id,
                watering_date=watering_date,
                humidity_before=current_humidity,
                humidity_after=None,  # 물주기 후 습도는 별도로 측정 필요
                humidity_increase=None,
                is_auto_detected=False,
                notes=watering_request.notes
            )
            
    except Exception as e:
        print(f"Error in record_manual_watering: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_plant_species_info(plant_idx: int, user_id: str) -> PlantSpeciesInfoResponse:
    """
    특정 식물의 품종 정보를 plant_wiki에서 조회합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        query = """
        SELECT 
            pw.name_jong as species,
            pw.feature,
            pw.temp,
            pw.watering,
            pw.flowering,
            pw.flower_color,
            pw.fertilizer,
            pw.pruning,
            pw.repot,
            pw.toxic
        FROM user_plant up
        LEFT JOIN plant_wiki pw ON up.plant_id = pw.wiki_plant_id
        WHERE up.idx = %s AND up.user_id = %s
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (plant_idx, user_id))
            result = await cursor.fetchone()
            
            if not result:
                raise ValueError("식물 정보를 찾을 수 없습니다.")
            
            return PlantSpeciesInfoResponse(
                species=result['species'] or "정보 없음",
                wiki_img=None,  # plant_wiki 테이블에 wiki_img 컬럼 없음
                feature=result['feature'],
                temp=result['temp'],
                watering=result['watering'],
                flowering=result['flowering'],
                flower_color=result['flower_color'],
                fertilizer=result['fertilizer'],
                pruning=result['pruning'],
                repot=result['repot'],
                toxic=result['toxic']
            )
            
    except Exception as e:
        print(f"Error in get_plant_species_info: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def update_watering_settings(plant_idx: int, user_id: str, settings: WateringSettingsRequest) -> WateringSettingsResponse:
    """
    식물의 물주기 설정을 업데이트합니다.
    DB 저장 없이 세션/메모리에서 처리합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        # 식물이 존재하는지 확인
        check_query = """
        SELECT idx FROM user_plant 
        WHERE idx = %s AND user_id = %s
        """
        
        async with connection.cursor() as cursor:
            await cursor.execute(check_query, (plant_idx, user_id))
            result = await cursor.fetchone()
            
            if not result:
                raise ValueError("식물을 찾을 수 없습니다.")
            
            # 임계값 범위 검증 (5-20% 사이)
            if not (5 <= settings.humidity_threshold <= 20):
                raise ValueError("습도 증가율 임계값은 5%에서 20% 사이여야 합니다.")
            
            # DB 저장 없이 성공 응답 반환
            return WateringSettingsResponse(
                plant_idx=plant_idx,
                user_id=user_id,
                humidity_threshold=settings.humidity_threshold,
                message=f"물주기 설정이 {settings.humidity_threshold}%로 설정되었습니다. (세션 저장)"
            )
                
    except Exception as e:
        print(f"Error in update_watering_settings: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_watering_settings(plant_idx: int, user_id: str) -> WateringSettingsResponse:
    """
    식물의 현재 물주기 설정을 조회합니다.
    기본값 10%를 반환합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        # 식물이 존재하는지 확인
        check_query = """
        SELECT idx FROM user_plant
        WHERE idx = %s AND user_id = %s
        """
        
        async with connection.cursor() as cursor:
            await cursor.execute(check_query, (plant_idx, user_id))
            result = await cursor.fetchone()
            
            if not result:
                raise ValueError("식물 정보를 찾을 수 없습니다.")
            
            # 기본값 10% 반환 (DB 저장 없이 세션에서 관리)
            threshold = 10  # 기본값 10%
            
            return WateringSettingsResponse(
                plant_idx=plant_idx,
                user_id=user_id,
                humidity_threshold=threshold,
                message=f"현재 물주기 설정: 습도 {threshold}% 증가 시 자동 기록 (기본값)"
            )
            
    except Exception as e:
        print(f"Error in get_watering_settings: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_plant_pest_records_by_user_plant(plant_idx: int, user_id: str) -> List[PlantPestRecordResponse]:
    """
    특정 유저의 특정 식물에 대한 병충해 기록을 조회합니다.
    새로운 user_plant_pest 테이블을 사용합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        # user_plant_pest와 pest_wiki를 조인하여 해당 식물의 병충해 기록 조회
        query = """
        SELECT 
            pw.pest_id,
            pw.pest_name,
            pw.cause,
            pw.cure,
            upp.idx as record_id,
            upp.pest_date as recorded_date
        FROM user_plant up
        JOIN user_plant_pest upp ON up.plant_id = upp.plant_id
        JOIN pest_wiki pw ON upp.pest_id = pw.pest_id
        WHERE up.idx = %s AND up.user_id = %s
        ORDER BY upp.pest_date DESC
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (plant_idx, user_id))
            results = await cursor.fetchall()
            
            pest_records = []
            for row in results:
                pest_record = PlantPestRecordResponse(
                    pest_id=row['pest_id'],
                    cause=row['cause'],
                    cure=row['cure'],
                    recorded_date=row['recorded_date']  # 현재 날짜 사용
                )
                pest_records.append(pest_record)
            
            return pest_records
            
    except Exception as e:
        print(f"Error in get_plant_pest_records_by_user_plant: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def add_plant_pest_record(plant_idx: int, user_id: str, pest_id: int, pest_date: str = None) -> dict:
    """
    식물에 병충해 기록을 추가합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        # 식물이 존재하는지 확인
        check_query = """
        SELECT plant_id FROM user_plant 
        WHERE idx = %s AND user_id = %s
        """
        
        async with connection.cursor() as cursor:
            await cursor.execute(check_query, (plant_idx, user_id))
            result = await cursor.fetchone()
            
            if not result:
                raise ValueError("식물을 찾을 수 없습니다.")
            
            plant_id = result[0]
            
            # 병충해 기록 추가
            insert_query = """
            INSERT INTO user_plant_pest (plant_id, pest_id, pest_date)
            VALUES (%s, %s, %s)
            """
            
            # 날짜가 제공되지 않으면 현재 날짜 사용
            if pest_date is None:
                pest_date = datetime.now().strftime('%Y-%m-%d')
            
            await cursor.execute(insert_query, (plant_id, pest_id, pest_date))
            await connection.commit()
            
            record_id = cursor.lastrowid
            
            return {
                "success": True,
                "record_id": record_id,
                "plant_id": plant_id,
                "pest_id": pest_id,
                "pest_date": pest_date,
                "message": "병충해 기록이 성공적으로 추가되었습니다."
            }
                
    except Exception as e:
        print(f"Error in add_plant_pest_record: {e}")
        raise e
    finally:
        if connection:
            connection.close()

async def get_plant_recent_diary_summary(plant_idx: int, user_id: str) -> dict:
    """
    특정 식물과 연관된 최근 일기의 제목과 작성 날짜를 조회합니다.
    """
    connection = None
    try:
        connection = await get_db_connection()
        
        query = """
        SELECT 
            d.diary_id,
            d.user_title,
            d.created_at
        FROM diary d
        JOIN user_plant up ON d.user_id = up.user_id
        WHERE up.idx = %s AND up.user_id = %s
        ORDER BY d.created_at DESC
        LIMIT 1
        """
        
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (plant_idx, user_id))
            result = await cursor.fetchone()
            
            if result:
                return {
                    "has_diary": True,
                    "latest_diary": {
                        "diary_id": result['diary_id'],
                        "title": result['user_title'],
                        "created_at": result['created_at']
                    }
                }
            else:
                return {
                    "has_diary": False,
                    "latest_diary": None,
                    "message": "작성한 일기가 없어요."
                }
            
    except Exception as e:
        print(f"Error in get_plant_recent_diary_summary: {e}")
        raise e
    finally:
        if connection:
            connection.close()
