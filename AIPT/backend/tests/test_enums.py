#!/usr/bin/env python3
"""
Enum 및 JSON 필드 회귀 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime
from sqlmodel import Session, create_engine, select
from models.models import Session as SessionModel, Event as EventModel
from models.database import engine, create_db_and_tables

@pytest.fixture(scope="function")
def db_session():
    """테스트용 데이터베이스 세션"""
    create_db_and_tables()
    with Session(engine) as session:
        yield session

def test_session_model_creation(db_session):
    """Session 모델 생성 테스트"""
    session = SessionModel(
        session_id="test_session_123",
        user_id="test_user",
        exercise_type="squat",
        started_at=datetime.now(),
        status="active"
    )
    
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    assert session.id is not None
    assert session.session_id == "test_session_123"
    assert session.status == "active"

def test_event_model_creation(db_session):
    """Event 모델 생성 테스트"""
    # 먼저 Session 생성
    session = SessionModel(
        session_id="test_session_456",
        user_id="test_user",
        exercise_type="pushup",
        started_at=datetime.now(),
        status="active"
    )
    db_session.add(session)
    db_session.commit()
    
    # Event 생성
    event = EventModel(
        session_id="test_session_456",
        exercise="pushup",
        rep_index=1,
        stage="up",
        angles={"knee": 90.0, "hip": 45.0},
        confidence=0.95
    )
    
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    
    assert event.id is not None
    assert event.angles == {"knee": 90.0, "hip": 45.0}
    assert event.confidence == 0.95

def test_json_field_operations(db_session):
    """JSON 필드 작업 테스트"""
    session = SessionModel(
        session_id="test_session_789",
        user_id="test_user",
        exercise_type="lunge",
        started_at=datetime.now(),
        feedback_summary={
            "form_score": 85.5,
            "issues": ["knee alignment", "depth"],
            "suggestions": ["keep knees behind toes", "go deeper"]
        }
    )
    
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    assert session.feedback_summary["form_score"] == 85.5
    assert "knee alignment" in session.feedback_summary["issues"]

def test_model_relationships(db_session):
    """모델 관계 테스트"""
    # Session 생성
    session = SessionModel(
        session_id="test_session_rel",
        user_id="test_user",
        exercise_type="bicep_curl",
        started_at=datetime.now(),
        status="active"
    )
    db_session.add(session)
    db_session.commit()
    
    # 여러 Event 생성
    events = [
        EventModel(
            session_id="test_session_rel",
            exercise="bicep_curl",
            rep_index=i,
            stage="up" if i % 2 == 0 else "down",
            angles={"elbow": 90.0 + i},
            confidence=0.9 + (i * 0.01)
        )
        for i in range(1, 4)
    ]
    
    for event in events:
        db_session.add(event)
    db_session.commit()
    
    # 관계 조회 테스트
    stmt = select(EventModel).where(EventModel.session_id == "test_session_rel")
    result = db_session.exec(stmt).all()
    
    assert len(result) == 3
    assert all(event.session_id == "test_session_rel" for event in result)

def test_enum_string_constants(db_session):
    """Enum 문자열 상수 테스트"""
    # SessionStatus 상수 테스트
    from models.models import SESSION_STATUS_ACTIVE, SESSION_STATUS_COMPLETED
    
    session = SessionModel(
        session_id="test_enum_session",
        user_id="test_user",
        exercise_type="shoulder_press",
        started_at=datetime.now(),
        status=SESSION_STATUS_ACTIVE
    )
    
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    assert session.status == SESSION_STATUS_ACTIVE
    
    # 상태 변경
    session.status = SESSION_STATUS_COMPLETED
    db_session.commit()
    db_session.refresh(session)
    
    assert session.status == SESSION_STATUS_COMPLETED

if __name__ == "__main__":
    # 직접 실행 시 테스트 실행
    pytest.main([__file__, "-v"])
