from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PlantStatusResponse(BaseModel):
    """식물 상태 정보 응답 스키마"""
    idx: int
    user_id: str
    plant_id: int
    plant_name: str  # 별명
    species: Optional[str] = None  # 품종
    pest_id: Optional[int] = None  # 건강 상태 (병해충 여부)
    meet_day: Optional[datetime] = None  # 만난날
    on: Optional[str] = None
    
    # 습도 정보
    current_humidity: Optional[float] = None
    humidity_date: Optional[datetime] = None
    
    # 품종별 최적 습도 범위
    optimal_min_humidity: Optional[int] = None
    optimal_max_humidity: Optional[int] = None
    humidity_status: Optional[str] = None  # "안전", "주의", "위험"
    
    # 식물 위키 정보
    wiki_img: Optional[str] = None  # 위키 이미지
    feature: Optional[str] = None
    temp: Optional[str] = None
    watering: Optional[str] = None
    
    # 병해충 정보
    pest_cause: Optional[str] = None
    pest_cure: Optional[str] = None
    
    # 사용자 식물 사진
    user_plant_image: Optional[str] = None

class DashboardResponse(BaseModel):
    """메인페이지 대시보드 응답 스키마"""
    user_id: str
    total_plants: int
    plants: List[PlantStatusResponse]
    message: str = "식물 정보를 성공적으로 조회했습니다."

class DashboardRequest(BaseModel):
    """메인페이지 대시보드 요청 스키마"""
    user_id: str
