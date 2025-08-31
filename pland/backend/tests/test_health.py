"""
Health Check Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """헬스체크 엔드포인트 테스트"""
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["service"] == "Plant Whisperer API"
    assert data["version"] == "1.0.0"


def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "1.0.0"
