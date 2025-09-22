#!/usr/bin/env python3
"""
모델 서버 연결 테스트
"""
import requests
import json

def test_model_server():
    """모델 서버 연결 테스트"""
    try:
        # 1. 헬스 체크
        print("🔍 모델 서버 헬스 체크...")
        response = requests.get("http://localhost:5000/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # 2. 병충해 진단 API 테스트 (더미 이미지)
        print("\n🔍 병충해 진단 API 테스트...")
        
        # 더미 이미지 파일 생성
        dummy_image_data = b"dummy_image_data"
        
        files = {
            'image': ('test.jpg', dummy_image_data, 'image/jpeg')
        }
        
        response = requests.post("http://localhost:5000/disease", files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    test_model_server()
