import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from datetime import datetime
import json

from main import app
from models.database import get_session
from models.models import Session as SessionModel, Event as EventModel

# 테스트용 인메모리 데이터베이스
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture
def client():
    SQLModel.metadata.create_all(engine)
    with TestClient(app) as test_client:
        yield test_client
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def session_data():
    return {
        "exercise_type": "squat",
        "target_reps": 10,
        "notes": "테스트 세션"
    }

@pytest.fixture
def event_data():
    return {
        "exercise": "squat",
        "rep_index": 1,
        "stage": "down",
        "angles": {"knee": 90.0, "hip": 45.0},
        "feedback_code": "GOOD_FORM",
        "danger_flag": False,
        "confidence": 0.85
    }

class TestHealthCheck:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

class TestSessionManagement:
    def test_start_session(self, client, session_data):
        response = client.post(
            "/api/sessions/start",
            json=session_data,
            headers={"user_id": "test_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["exercise_type"] == "squat"
        assert data["target_reps"] == 10
        assert data["status"] == "active"
        assert "session_id" in data

    def test_start_session_without_user_id(self, client, session_data):
        response = client.post("/api/sessions/start", json=session_data)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_123"  # 기본값

    def test_end_session(self, client, session_data):
        # 먼저 세션 시작
        start_response = client.post(
            "/api/sessions/start",
            json=session_data,
            headers={"user_id": "test_user"}
        )
        session_id = start_response.json()["session_id"]

        # 세션 종료
        end_data = {
            "total_reps": 8,
            "total_duration": 300,
            "form_score": 85.0,
            "status": "completed"
        }
        
        response = client.post(
            f"/api/sessions/{session_id}/end",
            json=end_data,
            headers={"user_id": "test_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_reps"] == 8
        assert data["status"] == "completed"

    def test_end_nonexistent_session(self, client):
        end_data = {"total_reps": 8, "status": "completed"}
        response = client.post(
            "/api/sessions/nonexistent/end",
            json=end_data,
            headers={"user_id": "test_user"}
        )
        assert response.status_code == 404

class TestEventManagement:
    def test_add_events(self, client, session_data, event_data):
        # 먼저 세션 시작
        start_response = client.post(
            "/api/sessions/start",
            json=session_data,
            headers={"user_id": "test_user"}
        )
        session_id = start_response.json()["session_id"]

        # 이벤트 추가
        events_batch = {"events": [event_data]}
        response = client.post(
            f"/api/sessions/{session_id}/events",
            json=events_batch,
            headers={"user_id": "test_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["events_processed"] == 1
        assert data["session_id"] == session_id

    def test_add_events_to_nonexistent_session(self, client, event_data):
        events_batch = {"events": [event_data]}
        response = client.post(
            "/api/sessions/nonexistent/events",
            json=events_batch,
            headers={"user_id": "test_user"}
        )
        assert response.status_code == 404

class TestSessionQueries:
    def test_get_sessions(self, client, session_data):
        # 세션 생성
        client.post(
            "/api/sessions/start",
            json=session_data,
            headers={"user_id": "test_user"}
        )

        # 세션 목록 조회
        response = client.get(
            "/api/sessions",
            headers={"user_id": "test_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["exercise_type"] == "squat"

    def test_get_sessions_with_filters(self, client, session_data):
        # 세션 생성
        client.post(
            "/api/sessions/start",
            json=session_data,
            headers={"user_id": "test_user"}
        )

        # 필터와 함께 조회
        response = client.get(
            "/api/sessions?exercise_type=squat&limit=10",
            headers={"user_id": "test_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 1

    def test_get_session_detail(self, client, session_data):
        # 세션 생성
        start_response = client.post(
            "/api/sessions/start",
            json=session_data,
            headers={"user_id": "test_user"}
        )
        session_id = start_response.json()["session_id"]

        # 세션 상세 조회
        response = client.get(
            f"/api/sessions/{session_id}",
            headers={"user_id": "test_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["exercise_type"] == "squat"

    def test_get_nonexistent_session_detail(self, client):
        response = client.get(
            "/api/sessions/nonexistent",
            headers={"user_id": "test_user"}
        )
        assert response.status_code == 404

class TestUserStats:
    def test_get_user_stats(self, client, session_data):
        # 세션 생성 및 종료
        start_response = client.post(
            "/api/sessions/start",
            json=session_data,
            headers={"user_id": "test_user"}
        )
        session_id = start_response.json()["session_id"]

        end_data = {
            "total_reps": 10,
            "total_duration": 300,
            "form_score": 85.0,
            "status": "completed"
        }
        client.post(
            f"/api/sessions/{session_id}/end",
            json=end_data,
            headers={"user_id": "test_user"}
        )

        # 통계 조회
        response = client.get("/api/users/test_user/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 1
        assert data["total_reps"] == 10
        assert data["total_duration"] == 300
        assert data["average_form_score"] == 85.0

    def test_get_user_stats_with_period_filter(self, client):
        response = client.get("/api/users/test_user/stats?period=month")
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert "total_reps" in data
        assert "total_duration" in data
        assert "average_form_score" in data
