from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PlantDetailResponse(BaseModel):
    """식물 상세 정보 응답 스키마"""
    idx: int
    user_id: str
    plant_id: int
    plant_name: str  # 별명
    species: Optional[str] = None  # 품종
    meet_day: Optional[datetime] = None  # 키우기 시작한날
    pest_id: Optional[int] = None  # 건강상태 (병해충 여부)
    on: Optional[str] = None
    
    # 습도 정보
    current_humidity: Optional[float] = None
    humidity_date: Optional[datetime] = None
    humidity_history: Optional[List[dict]] = None
    
    # 식물 위키 정보 (품종 정보)
    wiki_img: Optional[str] = None
    feature: Optional[str] = None
    temp: Optional[str] = None
    watering: Optional[str] = None
    flowering: Optional[str] = None
    flower_color: Optional[str] = None
    fertilizer: Optional[str] = None
    pruning: Optional[str] = None
    repot: Optional[str] = None
    toxic: Optional[str] = None
    
    # 병해충 정보
    pest_cause: Optional[str] = None
    pest_cure: Optional[str] = None
    
    # 사용자 식물 사진
    user_plant_image: Optional[str] = None
    
    # 일기 개수
    diary_count: int = 0
    
    # 키우는 장소 + 날씨 (향후 확장용)
    growing_location: Optional[str] = None
    weather: Optional[str] = None

class PlantDiaryResponse(BaseModel):
    """식물 일기 응답 스키마"""
    diary_id: int
    user_id: str
    user_title: str
    img_url: Optional[str] = None
    user_content: Optional[str] = None
    hashtag: Optional[str] = None
    plant_content: Optional[str] = None
    weather: Optional[str] = None
    created_at: datetime

class PlantPestRecordResponse(BaseModel):
    """식물 병해충 기록 응답 스키마"""
    pest_id: int
    cause: str
    cure: str
    recorded_date: Optional[datetime] = None

class PlantDeleteRequest(BaseModel):
    """식물 삭제 요청 스키마"""
    user_id: str
    plant_idx: int
    reason: Optional[str] = None  # 삭제 사유

class PlantUpdateRequest(BaseModel):
    """식물 정보 수정 요청 스키마"""
    plant_name: Optional[str] = None
    species: Optional[str] = None
    meet_day: Optional[datetime] = None
    growing_location: Optional[str] = None

class PlantDetailSummaryResponse(BaseModel):
    """식물 상세 요약 정보 응답 스키마"""
    plant_info: PlantDetailResponse
    recent_diaries: List[PlantDiaryResponse]
    pest_records: List[PlantPestRecordResponse]
    humidity_trend: Optional[str] = None  # "increasing", "decreasing", "stable"
    care_reminders: List[str] = []  # 관리 알림

class WateringRecordResponse(BaseModel):
    """물주기 기록 응답 스키마"""
    record_id: int
    plant_idx: int
    user_id: str
    watering_date: datetime
    humidity_before: Optional[float] = None
    humidity_after: Optional[float] = None
    humidity_increase: Optional[float] = None
    is_auto_detected: bool = False  # 자동 감지된 물주기인지 여부
    notes: Optional[str] = None

class WateringRecordRequest(BaseModel):
    """물주기 기록 요청 스키마"""
    plant_idx: int
    user_id: str
    watering_date: Optional[datetime] = None
    notes: Optional[str] = None

class HealthStatusResponse(BaseModel):
    """건강상태 응답 스키마"""
    plant_idx: int
    user_id: str
    overall_status: str  # "건강", "주의", "아픔"
    health_score: int  # 0-100 점수
    status_details: dict  # 상세 상태 정보
    
    # 개별 요소별 상태
    humidity_status: str  # "good", "low", "high"
    pest_status: str  # "healthy", "infected", "recovering"
    leaf_health_status: str  # "healthy", "warning", "sick"
    
    # 권장사항
    recommendations: List[str] = []
    urgent_actions: List[str] = []

class HealthAnalysisRequest(BaseModel):
    """건강상태 분석 요청 스키마"""
    plant_idx: int
    user_id: str
    leaf_health_score: Optional[float] = None  # AI 모델에서 받은 잎 건강 점수
    force_refresh: bool = False  # 강제 새로고침 여부
