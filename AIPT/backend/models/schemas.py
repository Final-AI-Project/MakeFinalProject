from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ExerciseStage(str, Enum):
    UP = "up"
    DOWN = "down"
    HOLD = "hold"

# Session 스키마
class SessionBase(BaseModel):
    exercise_type: str = Field(..., description="운동 타입")
    target_reps: Optional[int] = Field(None, description="목표 반복 횟수")
    notes: Optional[str] = Field(None, description="세션 노트")

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    ended_at: Optional[datetime] = None
    total_reps: Optional[int] = None
    total_duration: Optional[int] = None
    average_confidence: Optional[float] = None
    form_score: Optional[float] = None
    danger_events: Optional[int] = None
    feedback_summary: Optional[Dict[str, Any]] = None
    status: Optional[SessionStatus] = None
    notes: Optional[str] = None

class SessionResponse(SessionBase):
    session_id: str
    user_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_reps: Optional[int] = None
    total_duration: Optional[int] = None
    average_confidence: Optional[float] = None
    form_score: Optional[float] = None
    danger_events: Optional[int] = None
    feedback_summary: Optional[Dict[str, Any]] = None
    status: SessionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Event 스키마
class EventBase(BaseModel):
    exercise: str = Field(..., description="운동 타입")
    rep_index: int = Field(0, description="반복 인덱스")
    stage: ExerciseStage = Field(ExerciseStage.HOLD, description="운동 단계")
    angles: Dict[str, float] = Field(default_factory=dict, description="관절 각도")
    feedback_code: str = Field("", description="피드백 코드")
    danger_flag: bool = Field(False, description="위험 플래그")
    confidence: float = Field(0.0, description="포즈 신뢰도")

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: int
    session_id: str
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class EventBatch(BaseModel):
    events: List[EventCreate] = Field(..., description="이벤트 배치")

# 통계 스키마
class UserStats(BaseModel):
    total_sessions: int = Field(0, description="총 세션 수")
    total_reps: int = Field(0, description="총 반복 횟수")
    total_duration: int = Field(0, description="총 운동 시간(초)")
    average_form_score: float = Field(0.0, description="평균 폼 점수")
    favorite_exercise: Optional[str] = Field(None, description="가장 많이 한 운동")
    exercise_breakdown: Dict[str, int] = Field(default_factory=dict, description="운동별 통계")

# 응답 스키마
class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int
    page: int
    size: int

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

class SuccessResponse(BaseModel):
    message: str
    data: Optional[Any] = None
