#!/usr/bin/env python3
"""
간단한 테스트 - 단계별 확인
"""
import requests
import json

def test_basic():
    print("=== 기본 테스트 시작 ===")
    
    # 1. 백엔드 서버 확인
    try:
        response = requests.get("http://localhost:3000/healthcheck", timeout=5)
        print(f"✅ 백엔드 서버: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ 백엔드 서버: {e}")
        return
    
    # 2. DB 헬스체크
    try:
        response = requests.get("http://localhost:3000/health/db", timeout=5)
        print(f"✅ DB 연결: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ DB 연결: {e}")
    
    # 3. 모델 서버 확인
    try:
        response = requests.get("http://127.0.0.1:5000/health", timeout=10)
        print(f"✅ 모델 서버: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ 모델 서버: {e}")
    
    print("=== 기본 테스트 완료 ===")

if __name__ == "__main__":
    test_basic()
