import aiomysql
from typing import List, Optional
from datetime import datetime
from db.pool import get_db_connection
from schemas.dashboard import PlantStatusResponse, DashboardResponse

async def get_user_plants_with_status(user_id: str) -> DashboardResponse:
    """
    사용자의 모든 식물 정보와 상태를 조회합니다.
    습도 정보와 식물 위키 정보, 병해충 정보를 포함합니다.
    """
    async with get_db_connection() as (conn, cursor):
        
        # 단순한 쿼리로 복원 (식물 목록만 먼저 표시)
        query = """
        SELECT 
            up.plant_id,
            up.user_id,
            up.plant_name,
            up.species,
            up.meet_day,
            -- 사용자 식물 사진 (img_address 테이블의 이미지 - 첫 번째 이미지)
            (SELECT ia.img_url 
             FROM img_address ia 
             WHERE ia.plant_id = up.plant_id 
             ORDER BY ia.img_url 
             LIMIT 1) as user_plant_image,
            -- 최신 습도 정보 (humid 테이블에서 직접 조회, device_id=1 공통 사용)
            (SELECT h.humidity 
             FROM humid h 
             WHERE h.device_id = 1 
             ORDER BY h.humid_date DESC 
             LIMIT 1) as current_humidity,
             
            -- 최신 습도 측정 시간
            (SELECT h.humid_date 
             FROM humid h 
             WHERE h.device_id = 1 
             ORDER BY h.humid_date DESC 
             LIMIT 1) as humidity_date,
             
            -- 습도 데이터 존재 여부 확인
            (SELECT COUNT(*) 
             FROM humid h 
             WHERE h.device_id = 1) as humidity_data_count,
            -- 품종별 최적 습도 범위 (plant_wiki와 best_humid 조인)
            (SELECT bh.min_humid 
             FROM plant_wiki pw 
             JOIN best_humid bh ON pw.wiki_plant_id = bh.wiki_plant_id
             WHERE (pw.sci_name LIKE CONCAT('%%', up.species, '%%') OR up.species LIKE CONCAT('%%', TRIM(SUBSTRING_INDEX(pw.sci_name, '(', 1)), '%%'))
             LIMIT 1) as min_humid,
             
            (SELECT bh.max_humid 
             FROM plant_wiki pw 
             JOIN best_humid bh ON pw.wiki_plant_id = bh.wiki_plant_id
             WHERE (pw.sci_name LIKE CONCAT('%%', up.species, '%%') OR up.species LIKE CONCAT('%%', TRIM(SUBSTRING_INDEX(pw.sci_name, '(', 1)), '%%'))
             LIMIT 1) as max_humid,
             
            (SELECT pw.sci_name 
             FROM plant_wiki pw 
             WHERE (pw.sci_name LIKE CONCAT('%%', up.species, '%%') OR up.species LIKE CONCAT('%%', TRIM(SUBSTRING_INDEX(pw.sci_name, '(', 1)), '%%'))
             LIMIT 1) as sci_name,
            0 as active_pest_count
        FROM user_plant up
        WHERE up.user_id = %s
        ORDER BY up.meet_day DESC
        """
        
        await cursor.execute(query, (user_id,))
        results = await cursor.fetchall()
        
        print(f"[DEBUG] 대시보드 쿼리 결과: {len(results)}개 식물 조회됨")
        for i, row in enumerate(results):
            print(f"[DEBUG] 식물 {i+1}: {row.get('plant_name')} - 품종: {row.get('species')}, 최적범위: {row.get('min_humid')}-{row.get('max_humid')}%")
        
        plants = []
        for row in results:
            # 습도 데이터 검증 및 처리
            humidity_data_count = row.get('humidity_data_count', 0)
            current_humidity = row.get('current_humidity')
            humidity_date = row.get('humidity_date')
            
            # 품종별 최적 습도 범위 가져오기
            min_humidity = row.get('min_humid')
            max_humidity = row.get('max_humid')
            
            # 습도 데이터 검증 로직
            if humidity_data_count == 0:
                # 습도 데이터가 전혀 없는 경우
                humidity = 50  # 기본값
                print(f"[DEBUG] 식물 {row['plant_id']}: 습도 데이터 없음, 기본값 50% 사용")
            elif current_humidity is None:
                # 습도 데이터가 없는 경우
                humidity = 50  # 기본값
                print(f"[DEBUG] 식물 {row['plant_id']}: 습도 데이터 없음, 기본값 50% 사용")
            else:
                # 실제 습도 데이터가 있는 경우 (0값도 포함)
                humidity = int(current_humidity)
                # 습도 데이터 신선도 검증
                freshness_info = await validate_humidity_data_freshness(row['plant_id'])
                if not freshness_info['is_fresh']:
                    print(f"[WARNING] 식물 {row['plant_id']}: 습도 데이터가 오래됨 - {freshness_info['message']}")
                print(f"[DEBUG] 식물 {row['plant_id']}: 실제 습도 데이터 사용 - {humidity}% (측정시간: {humidity_date}, 신선도: {freshness_info['message']})")
            
            # 품종별 습도 범위가 있는 경우 상태 결정
            humidity_status = None
            if min_humidity is not None and max_humidity is not None:
                status_info = determine_humidity_status(humidity, min_humidity, max_humidity)
                humidity_status = status_info['status']
                print(f"[DEBUG] 식물 {row['plant_id']} ({row['species']}): {status_info['status']} - {status_info['description']} (현재: {humidity}%, 적정: {status_info['optimal_range']})")
            else:
                print(f"[DEBUG] 식물 {row['plant_id']} ({row['species']}): 품종별 습도 범위 정보 없음 - 적정 범위 표시 안함")
                # DB에 데이터가 없는 경우 null로 설정 (표시하지 않음)
                min_humidity = None
                max_humidity = None
                humidity_status = None
            
            # 병충해 정보 가져오기
            active_pest_count = row.get('active_pest_count', 0)
            
            # 전체 건강 상태 계산 (습도 + 병충해) - 임시 비활성화
            # try:
            #     health_status = determine_plant_health_status(humidity, min_humidity, max_humidity, active_pest_count)
            #     print(f"[DEBUG] 식물 {row['plant_id']} 건강상태: {health_status['status']} - {health_status['description']} (습도: {humidity_status}, 병충해: {active_pest_count}개)")
            # except Exception as e:
            #     print(f"[ERROR] 식물 {row['plant_id']} 건강상태 계산 오류: {e}")
            #     health_status = {"status": "건강", "color": "green", "description": "기본값"}
            
            # 임시로 기본값 사용
            health_status = {"status": "건강", "color": "green", "description": "기본값"}
            print(f"[DEBUG] 식물 {row['plant_id']} 건강상태: 임시 기본값 사용")
            
            plant = PlantStatusResponse(
                idx=row['plant_id'],  # plant_id가 실제 primary key
                user_id=row['user_id'],
                plant_id=row['plant_id'],
                plant_name=row['plant_name'],
                species=row['species'],
                pest_id=None,
                meet_day=row['meet_day'],
                on=None,  # location은 사용하지 않으므로 None
                current_humidity=humidity,  # 검증된 습도 데이터
                humidity_date=humidity_date,  # 실제 측정 시간 또는 None
                optimal_min_humidity=min_humidity,  # 품종별 최소 습도
                optimal_max_humidity=max_humidity,  # 품종별 최대 습도
                humidity_status=humidity_status,  # 습도 상태 ("안전", "주의", "위험")
                health_status=health_status['status'],  # 전체 건강 상태 ("건강", "주의", "아픔")
                wiki_img=None,
                feature=None,
                temp=None,
                watering=None,
                pest_cause=None,
                pest_cure=None,
                user_plant_image=row['user_plant_image']  # 실제 이미지 URL 사용
            )
            plants.append(plant)
        
        return DashboardResponse(
            user_id=user_id,
            total_plants=len(plants),
            plants=plants
        )

async def get_plant_humidity_history(plant_id: int, limit: int = 7) -> List[dict]:
    """
    특정 식물의 최근 습도 기록을 조회합니다.
    """
    async with get_db_connection() as (conn, cursor):
        query = """
        SELECT 
            humidity,
            humid_date
        FROM humid
        WHERE device_id = 1
        ORDER BY humid_date DESC
        LIMIT %s
        """
        
        await cursor.execute(query, (limit,))
        results = await cursor.fetchall()
        return results

async def get_plant_diary_count(plant_id: int) -> int:
    """
    특정 식물의 일기 개수를 조회합니다.
    """
    async with get_db_connection() as (conn, cursor):
        query = """
        SELECT COUNT(*) as count
        FROM diary d
        JOIN user_plant up ON d.user_id = up.user_id
        WHERE up.plant_id = %s
        """
        
        await cursor.execute(query, (plant_id,))
        result = await cursor.fetchone()
        return result['count'] if result else 0

async def validate_humidity_data_freshness(plant_id: int) -> dict:
    """
    특정 식물의 습도 데이터 신선도를 검증합니다.
    """
    async with get_db_connection() as (conn, cursor):
        query = """
        SELECT 
            h.humidity,
            h.humid_date,
            TIMESTAMPDIFF(MINUTE, h.humid_date, NOW()) as minutes_ago
        FROM humid h 
        WHERE h.device_id = 1 
        ORDER BY h.humid_date DESC 
        LIMIT 1
        """
        
        await cursor.execute(query)
        result = await cursor.fetchone()
        
        if not result:
            return {
                "has_data": False,
                "humidity": None,
                "humidity_date": None,
                "minutes_ago": None,
                "is_fresh": False,
                "message": "습도 데이터가 없습니다"
            }
        
        minutes_ago = result['minutes_ago']
        is_fresh = minutes_ago <= 60  # 1시간 이내 데이터를 신선한 것으로 간주
        
        return {
            "has_data": True,
            "humidity": result['humidity'],
            "humidity_date": result['humid_date'],
            "minutes_ago": minutes_ago,
            "is_fresh": is_fresh,
            "message": f"{minutes_ago}분 전 데이터" + (" (신선함)" if is_fresh else " (오래됨)")
        }

async def get_plant_optimal_humidity_range(plant_id: int) -> dict:
    """
    특정 식물의 품종별 최적 습도 범위를 DB에서 가져옵니다.
    """
    async with get_db_connection() as (conn, cursor):
        query = """
        SELECT 
            bh.min_humid,
            bh.max_humid,
            pw.sci_name,
            up.species
        FROM user_plant up
        LEFT JOIN plant_wiki pw ON up.species = pw.name_jong
        LEFT JOIN best_humid bh ON pw.wiki_plant_id = bh.wiki_plant_id
        WHERE up.plant_id = %s
        """
        
        await cursor.execute(query, (plant_id,))
        result = await cursor.fetchone()
        
        if result and result['min_humid'] is not None and result['max_humid'] is not None:
            return {
                "has_range": True,
                "min_humidity": result['min_humid'],
                "max_humidity": result['max_humid'],
                "sci_name": result['sci_name'],
                "species": result['species']
            }
        else:
            # DB에서 범위를 찾을 수 없는 경우 기본값 사용
            return {
                "has_range": False,
                "min_humidity": 30,
                "max_humidity": 70,
                "sci_name": None,
                "species": result['species'] if result else None
            }

def determine_humidity_status(current_humidity: int, min_humidity: int, max_humidity: int) -> dict:
    """
    현재 습도와 최적 범위를 비교하여 상태를 결정합니다.
    
    위험(빨간점): 적정 범위를 완전히 벗어난 경우
    주의(노란점): 적정 범위 ±5% 가까워진 경우  
    안전(초록점): 적정 범위 내부에 안정적으로 있는 경우
    """
    # ±5% 마진 계산
    caution_min = min_humidity - 5
    caution_max = max_humidity + 5
    
    if current_humidity < min_humidity or current_humidity > max_humidity:
        # 적정 범위를 완전히 벗어난 경우 - 위험
        status = "위험"
        color = "red"
        description = "적정 범위를 벗어남"
    elif current_humidity < caution_min or current_humidity > caution_max:
        # 적정 범위 ±5% 가까워진 경우 - 주의
        status = "주의"
        color = "yellow"
        description = "적정 범위 경계 근처"
    else:
        # 적정 범위 내부에 안정적으로 있는 경우 - 안전
        status = "안전"
        color = "green"
        description = "적정 범위 내"
    
    return {
        "status": status,
        "color": color,
        "description": description,
        "current_humidity": current_humidity,
        "optimal_range": f"{min_humidity}-{max_humidity}%",
        "caution_range": f"{caution_min}-{caution_max}%"
    }

def determine_plant_health_status(current_humidity: int, min_humidity: Optional[int], max_humidity: Optional[int], active_pest_count: int) -> dict:
    """
    현재 습도와 병충해 정보를 종합하여 식물의 전체 건강 상태를 결정합니다.
    
    건강(초록): 습도 적정 + 병충해 없음
    주의(노랑): 습도 주의 + 병충해 없음 또는 습도 적정 + 병충해 1개
    아픔(빨강): 습도 위험 또는 병충해 2개 이상
    """
    # 습도 상태 계산
    humidity_score = 0  # 0: 위험, 1: 주의, 2: 안전
    if min_humidity is not None and max_humidity is not None:
        humidity_status = determine_humidity_status(current_humidity, min_humidity, max_humidity)
        if humidity_status['status'] == "안전":
            humidity_score = 2
        elif humidity_status['status'] == "주의":
            humidity_score = 1
        else:  # 위험
            humidity_score = 0
    else:
        # 습도 범위 정보가 없는 경우 기본값으로 안전으로 간주
        humidity_score = 2
    
    # 병충해 점수 계산
    pest_score = 0  # 0: 많음(2개 이상), 1: 적음(1개), 2: 없음(0개)
    if active_pest_count >= 2:
        pest_score = 0
    elif active_pest_count == 1:
        pest_score = 1
    else:
        pest_score = 2
    
    # 종합 점수 계산 (습도 50% + 병충해 50%)
    total_score = (humidity_score + pest_score) / 2
    
    # 건강 상태 결정
    if total_score >= 1.5:
        # 건강: 습도 안전 + 병충해 없음 또는 습도 주의 + 병충해 없음
        status = "건강"
        color = "green"
        description = "건강한 상태"
    elif total_score >= 0.5:
        # 주의: 습도 주의 + 병충해 없음 또는 습도 안전 + 병충해 1개
        status = "주의"
        color = "yellow"
        description = "주의가 필요한 상태"
    else:
        # 아픔: 습도 위험 또는 병충해 2개 이상
        status = "아픔"
        color = "red"
        description = "치료가 필요한 상태"
    
    return {
        "status": status,
        "color": color,
        "description": description,
        "humidity_score": humidity_score,
        "pest_score": pest_score,
        "total_score": total_score,
        "active_pest_count": active_pest_count
    }
