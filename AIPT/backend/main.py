from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from typing import List, Optional
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

from models.database import engine, create_db_and_tables
from models.schemas import (
    SessionCreate, SessionResponse, SessionUpdate,
    EventCreate, EventResponse, EventBatch,
    UserStats, SessionListResponse
)
from models.models import Session as SessionModel, Event as EventModel

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="실시간 웹캠 운동 코치 API",
    description="웹캠 기반 실시간 운동 자세 분석 및 피드백 API",
    version="1.0.0"
)

# CORS 설정
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 의존성
def get_session():
    with Session(engine) as session:
        yield session

# 사용자 ID 검증 (간단한 구현)
def get_user_id(user_id: Optional[str] = Header(None)) -> str:
    if not user_id:
        user_id = "test_user_123"  # 기본 사용자 ID
    return user_id

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 데이터베이스 초기화"""
    create_db_and_tables()
    logger.info("✅ 백엔드 서버가 시작되었습니다.")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "실시간 웹캠 운동 코치 API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# 세션 관리 API
@app.post("/api/sessions/start", response_model=SessionResponse)
async def start_session(
    session_data: SessionCreate,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):
    """운동 세션 시작"""
    try:
        db_session = SessionModel(
            session_id=f"sess_{int(datetime.now().timestamp() * 1000)}",
            user_id=user_id,
            exercise_type=session_data.exercise_type,
            started_at=datetime.now(),
            target_reps=session_data.target_reps,
            notes=session_data.notes,
            status="active"
        )
        
        session.add(db_session)
        session.commit()
        session.refresh(db_session)
        
        logger.info(f"세션 시작: {db_session.session_id}")
        
        return SessionResponse(
            session_id=db_session.session_id,
            user_id=db_session.user_id,
            exercise_type=db_session.exercise_type,
            started_at=db_session.started_at,
            ended_at=db_session.ended_at,
            total_reps=db_session.total_reps,
            total_duration=db_session.total_duration,
            average_confidence=db_session.average_confidence,
            form_score=db_session.form_score,
            danger_events=db_session.danger_events,
            feedback_summary=db_session.feedback_summary,
            status=db_session.status,
            target_reps=db_session.target_reps,
            notes=db_session.notes,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at
        )
    except Exception as e:
        logger.error(f"세션 시작 실패: {e}")
        raise HTTPException(status_code=500, detail="세션 시작에 실패했습니다.")

@app.post("/api/sessions/{session_id}/events")
async def add_events(
    session_id: str,
    event_batch: EventBatch,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):
    """이벤트 배치 추가"""
    try:
        # 세션 존재 확인
        db_session = session.exec(
            select(SessionModel).where(SessionModel.session_id == session_id)
        ).first()
        
        if not db_session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 이벤트 추가
        events = []
        for event_data in event_batch.events:
            event = EventModel(
                session_id=session_id,
                timestamp=datetime.now(),
                exercise=event_data.exercise,
                rep_index=event_data.rep_index,
                stage=event_data.stage,
                angles=event_data.angles,
                feedback_code=event_data.feedback_code,
                danger_flag=event_data.danger_flag,
                confidence=event_data.confidence
            )
            events.append(event)
        
        session.add_all(events)
        session.commit()
        
        logger.info(f"이벤트 추가: {session_id}, {len(events)}개")
        
        return {
            "events_processed": len(events),
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이벤트 추가 실패: {e}")
        raise HTTPException(status_code=500, detail="이벤트 추가에 실패했습니다.")

@app.post("/api/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: str,
    session_update: SessionUpdate,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):
    """운동 세션 종료"""
    try:
        db_session = session.exec(
            select(SessionModel).where(SessionModel.session_id == session_id)
        ).first()
        
        if not db_session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 세션 업데이트
        db_session.ended_at = datetime.now()
        db_session.total_reps = session_update.total_reps
        db_session.total_duration = session_update.total_duration
        db_session.average_confidence = session_update.average_confidence
        db_session.form_score = session_update.form_score
        db_session.status = "completed"
        
        session.add(db_session)
        session.commit()
        session.refresh(db_session)
        
        logger.info(f"세션 종료: {session_id}")
        
        return SessionResponse(
            session_id=db_session.session_id,
            user_id=db_session.user_id,
            exercise_type=db_session.exercise_type,
            started_at=db_session.started_at,
            ended_at=db_session.ended_at,
            total_reps=db_session.total_reps,
            total_duration=db_session.total_duration,
            average_confidence=db_session.average_confidence,
            form_score=db_session.form_score,
            danger_events=db_session.danger_events,
            feedback_summary=db_session.feedback_summary,
            status=db_session.status,
            target_reps=db_session.target_reps,
            notes=db_session.notes,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"세션 종료 실패: {e}")
        raise HTTPException(status_code=500, detail="세션 종료에 실패했습니다.")

@app.get("/api/sessions", response_model=SessionListResponse)
async def get_sessions(
    user_id: str = Depends(get_user_id),
    limit: int = 20,
    offset: int = 0,
    exercise_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """세션 목록 조회"""
    try:
        query = select(SessionModel).where(SessionModel.user_id == user_id)
        
        # 필터 적용
        if exercise_type:
            query = query.where(SessionModel.exercise_type == exercise_type)
        
        if date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.where(SessionModel.started_at >= date_from_dt)
        
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.where(SessionModel.started_at <= date_to_dt)
        
        # 정렬 및 페이징
        query = query.order_by(SessionModel.started_at.desc())
        query = query.offset(offset).limit(limit)
        
        sessions = session.exec(query).all()
        
        # 전체 개수 조회
        count_query = select(SessionModel).where(SessionModel.user_id == user_id)
        if exercise_type:
            count_query = count_query.where(SessionModel.exercise_type == exercise_type)
        total_count = len(session.exec(count_query).all())
        
        return SessionListResponse(
            sessions=[
                SessionResponse(
                    session_id=s.session_id,
                    user_id=s.user_id,
                    exercise_type=s.exercise_type,
                    started_at=s.started_at,
                    ended_at=s.ended_at,
                    total_reps=s.total_reps,
                    total_duration=s.total_duration,
                    average_confidence=s.average_confidence,
                    form_score=s.form_score,
                    danger_events=s.danger_events,
                    feedback_summary=s.feedback_summary,
                    status=s.status,
                    target_reps=s.target_reps,
                    notes=s.notes,
                    created_at=s.created_at,
                    updated_at=s.updated_at
                )
                for s in sessions
            ],
            total=total_count,
            page=offset // limit + 1,
            size=limit
        )
    except Exception as e:
        logger.error(f"세션 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="세션 목록 조회에 실패했습니다.")

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session_detail(
    session_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id)
):
    """세션 상세 조회"""
    try:
        db_session = session.exec(
            select(SessionModel).where(
                SessionModel.session_id == session_id,
                SessionModel.user_id == user_id
            )
        ).first()
        
        if not db_session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 이벤트 조회
        events = session.exec(
            select(EventModel).where(EventModel.session_id == session_id)
        ).all()
        
        return SessionResponse(
            session_id=db_session.session_id,
            user_id=db_session.user_id,
            exercise_type=db_session.exercise_type,
            started_at=db_session.started_at,
            ended_at=db_session.ended_at,
            total_reps=db_session.total_reps,
            total_duration=db_session.total_duration,
            average_confidence=db_session.average_confidence,
            form_score=db_session.form_score,
            danger_events=db_session.danger_events,
            feedback_summary=db_session.feedback_summary,
            status=db_session.status,
            target_reps=db_session.target_reps,
            notes=db_session.notes,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"세션 상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="세션 상세 조회에 실패했습니다.")

@app.get("/api/users/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: str,
    period: str = "month",
    exercise_type: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """사용자 통계 조회"""
    try:
        # 기간 필터 계산
        now = datetime.now()
        if period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = datetime.min
        
        # 기본 쿼리
        query = select(SessionModel).where(
            SessionModel.user_id == user_id,
            SessionModel.started_at >= start_date
        )
        
        if exercise_type:
            query = query.where(SessionModel.exercise_type == exercise_type)
        
        sessions = session.exec(query).all()
        
        # 통계 계산
        total_sessions = len(sessions)
        total_reps = sum(s.total_reps or 0 for s in sessions)
        total_duration = sum(s.total_duration or 0 for s in sessions)
        
        form_scores = [s.form_score for s in sessions if s.form_score is not None]
        average_form_score = sum(form_scores) / len(form_scores) if form_scores else 0
        
        # 운동별 통계
        exercise_breakdown = {}
        for s in sessions:
            if s.exercise_type not in exercise_breakdown:
                exercise_breakdown[s.exercise_type] = {
                    "sessions": 0,
                    "reps": 0,
                    "avg_score": 0
                }
            
            exercise_breakdown[s.exercise_type]["sessions"] += 1
            exercise_breakdown[s.exercise_type]["reps"] += s.total_reps or 0
            
            if s.form_score:
                current_avg = exercise_breakdown[s.exercise_type]["avg_score"]
                current_count = exercise_breakdown[s.exercise_type]["sessions"]
                exercise_breakdown[s.exercise_type]["avg_score"] = (
                    (current_avg * (current_count - 1) + s.form_score) / current_count
                )
        
        # 가장 많이 한 운동 찾기
        favorite_exercise = None
        if exercise_breakdown:
            favorite_exercise = max(exercise_breakdown.keys(), 
                                  key=lambda x: exercise_breakdown[x]["sessions"])
        
        return UserStats(
            total_sessions=total_sessions,
            total_reps=total_reps,
            total_duration=total_duration,
            average_form_score=average_form_score,
            favorite_exercise=favorite_exercise,
            exercise_breakdown={k: v["sessions"] for k, v in exercise_breakdown.items()}
        )
    except Exception as e:
        logger.error(f"사용자 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="사용자 통계 조회에 실패했습니다.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
