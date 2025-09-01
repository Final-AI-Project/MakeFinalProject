from sqlmodel import SQLModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import JSON, Column

# Enum 대신 문자열 상수 사용
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_COMPLETED = "completed"
SESSION_STATUS_CANCELLED = "cancelled"

EXERCISE_STAGE_UP = "up"
EXERCISE_STAGE_DOWN = "down"
EXERCISE_STAGE_HOLD = "hold"

class Session(SQLModel, table=True):
    """운동 세션 모델"""
    __tablename__ = "sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(unique=True, index=True)
    user_id: str = Field(index=True)
    exercise_type: str = Field(index=True)
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = Field(default=None)
    target_reps: Optional[int] = Field(default=None)
    total_reps: Optional[int] = Field(default=None)
    total_duration: Optional[int] = Field(default=None)  # 초 단위
    average_confidence: Optional[float] = Field(default=None)
    form_score: Optional[float] = Field(default=None)  # 0-100
    danger_events: Optional[int] = Field(default=None)
    feedback_summary: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default=SESSION_STATUS_ACTIVE)
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Event(SQLModel, table=True):
    """운동 이벤트 모델"""
    __tablename__ = "events"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.session_id", index=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    exercise: str = Field(index=True)
    rep_index: int = Field(default=0)
    stage: str = Field(default=EXERCISE_STAGE_HOLD)
    angles: Dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))
    feedback_code: str = Field(default="")
    danger_flag: bool = Field(default=False)
    confidence: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.now)
