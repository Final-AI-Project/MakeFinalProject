from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PlantWikiInfo(BaseModel):
    """식물 위키 정보 스키마"""
    wiki_plant_id: int
    name_jong: str  # 종명
    feature: Optional[str] = None  # 특징
    temp: Optional[str] = None  # 온도
    watering: Optional[str] = None  # 물주기
    flowering: Optional[str] = None  # 개화
    flower_color: Optional[str] = None  # 꽃색
    fertilizer: Optional[str] = None  # 비료
    pruning: Optional[str] = None  # 가지치기
    repot: Optional[str] = None  # 분갈이
    toxic: Optional[str] = None  # 독성

class PestWikiInfo(BaseModel):
    """병충해 위키 정보 스키마"""
    pest_id: int
    pest_name: str  # 병충해명
    cause: Optional[str] = None  # 원인
    cure: Optional[str] = None  # 치료법
    prevention: Optional[str] = None  # 예방법

class PlantWikiListResponse(BaseModel):
    """식물 위키 목록 응답 스키마"""
    plants: List[PlantWikiInfo]
    total_count: int
    page: int
    limit: int

class PestWikiListResponse(BaseModel):
    """병충해 위키 목록 응답 스키마"""
    pests: List[PestWikiInfo]
    total_count: int
    page: int
    limit: int

class PlantWikiDetailResponse(BaseModel):
    """식물 위키 상세 정보 응답 스키마"""
    wiki_plant_id: int
    name_jong: str
    feature: Optional[str] = None
    temp: Optional[str] = None
    watering: Optional[str] = None
    flowering: Optional[str] = None
    flower_color: Optional[str] = None
    fertilizer: Optional[str] = None
    pruning: Optional[str] = None
    repot: Optional[str] = None
    toxic: Optional[str] = None

class PestWikiDetailResponse(BaseModel):
    """병충해 위키 상세 정보 응답 스키마"""
    pest_id: int
    pest_name: str
    cause: Optional[str] = None
    cure: Optional[str] = None
    prevention: Optional[str] = None

class InfoRoomStatsResponse(BaseModel):
    """정보방 통계 응답 스키마"""
    total_plants: int
    total_pests: int
    last_updated: Optional[datetime] = None

class PlantInfoResponse(BaseModel):
    """식물 정보 응답 스키마"""
    wiki_plant_id: int
    name_jong: str
    feature: Optional[str] = None
    temp: Optional[str] = None
    watering: Optional[str] = None
    flowering: Optional[str] = None
    flower_color: Optional[str] = None
    fertilizer: Optional[str] = None
    pruning: Optional[str] = None
    repot: Optional[str] = None
    toxic: Optional[str] = None

class PlantInfoListResponse(BaseModel):
    """식물 정보 목록 응답 스키마"""
    plants: List[PlantInfoResponse]
    total_count: int
    page: int
    limit: int

class PlantInfoSearchRequest(BaseModel):
    """식물 정보 검색 요청 스키마"""
    query: str
    species: Optional[str] = None