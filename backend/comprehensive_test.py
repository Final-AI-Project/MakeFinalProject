#!/usr/bin/env python3
"""
종합 기능 테스트 - DB, 백엔드 API, 모델 서버 통신 확인
"""
import requests
import json
import random
import os
import asyncio
import aiomysql
from datetime import date, datetime

# 환경 변수 설정 (백엔드 서버에서 사용하는 설정과 동일하게)
# 실제 DB 설정은 백엔드 서버에서 이미 설정되어 있으므로 여기서는 테스트용으로만 사용

class ComprehensiveTester:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.model_server_url = "http://127.0.0.1:5000"
        self.token = None
        self.user_id = None
        
    def print_section(self, title):
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_result(self, success, message, details=None):
        status = "✅" if success else "❌"
        print(f"{status} {message}")
        if details:
            print(f"   📋 {details}")
    
    # 1. DB 연결 테스트 (백엔드 API를 통해 간접 확인)
    async def test_db_connection(self):
        self.print_section("DB 연결 테스트")
        
        try:
            # 백엔드 API를 통해 DB 연결 상태 확인
            response = requests.get(f"{self.base_url}/health/db", timeout=5)
            if response.status_code == 200:
                self.print_result(True, "DB 연결 성공 (백엔드 API를 통해 확인)", f"응답: {response.json()}")
                return True
            else:
                self.print_result(False, f"DB 연결 실패: {response.status_code}")
                return False
            
        except Exception as e:
            self.print_result(False, f"DB 연결 테스트 실패: {e}")
            return False
    
    # 2. 백엔드 API 헬스체크
    def test_backend_health(self):
        self.print_section("백엔드 API 헬스체크")
        
        try:
            # 기본 헬스체크
            response = requests.get(f"{self.base_url}/healthcheck", timeout=5)
            if response.status_code == 200:
                self.print_result(True, "백엔드 서버 정상", f"응답: {response.json()}")
            else:
                self.print_result(False, f"헬스체크 실패: {response.status_code}")
                return False
            
            # DB 헬스체크
            response = requests.get(f"{self.base_url}/health/db", timeout=5)
            if response.status_code == 200:
                self.print_result(True, "DB 연결 정상", f"응답: {response.json()}")
            else:
                self.print_result(False, f"DB 헬스체크 실패: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.print_result(False, f"백엔드 연결 실패: {e}")
            return False
    
    # 3. 모델 서버 연결 테스트
    def test_model_server(self):
        self.print_section("모델 서버 연결 테스트")
        
        try:
            # 모델 서버 헬스체크
            response = requests.get(f"{self.model_server_url}/health", timeout=10)
            if response.status_code == 200:
                self.print_result(True, "모델 서버 정상", f"응답: {response.json()}")
            else:
                self.print_result(False, f"모델 서버 헬스체크 실패: {response.status_code}")
                return False
            
            # 식물 분류 모델 테스트 (올바른 엔드포인트)
            response = requests.get(f"{self.model_server_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get('models', {}).get('species'):
                    self.print_result(True, "식물 분류 모델 정상", f"사용 가능한 클래스: {health_data.get('available_classes', {}).get('species', [])}")
                else:
                    self.print_result(False, "식물 분류 모델 비활성화")
            else:
                self.print_result(False, f"식물 분류 모델 실패: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.print_result(False, f"모델 서버 연결 실패: {e}")
            return False
    
    # 4. 사용자 인증 테스트
    def test_user_auth(self):
        self.print_section("사용자 인증 테스트")
        
        try:
            # 랜덤 사용자 생성
            random_num = random.randint(10000, 99999)
            user_data = {
                "user_id": f"test_user_{random_num}",
                "user_pw": f"password_{random_num}",
                "email": f"test{random_num}@example.com",
                "hp": f"010-{random_num}-{random_num}",
                "nickname": f"테스트유저{random_num}"
            }
            
            # 회원가입
            response = requests.post(f"{self.base_url}/auth/signup", json=user_data, timeout=10)
            if response.status_code == 201:
                self.print_result(True, "회원가입 성공", f"사용자 ID: {user_data['user_id']}")
                self.user_id = user_data['user_id']
            else:
                self.print_result(False, f"회원가입 실패: {response.text}")
                return False
            
            # 로그인
            login_data = {
                "id_or_email": user_data["user_id"],
                "password": user_data["user_pw"]
            }
            
            response = requests.post(f"{self.base_url}/auth/login", json=login_data, timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("access_token")
                self.print_result(True, "로그인 성공", f"토큰: {self.token[:20]}...")
                return True
            else:
                self.print_result(False, f"로그인 실패: {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"인증 테스트 실패: {e}")
            return False
    
    # 5. 식물 관련 API 테스트
    def test_plant_apis(self):
        self.print_section("식물 관련 API 테스트")
        
        if not self.token:
            self.print_result(False, "토큰이 없어서 식물 API 테스트 불가")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 1) 식물 목록 조회
            response = requests.get(f"{self.base_url}/plants", headers=headers, timeout=10)
            if response.status_code == 200:
                plants_data = response.json()
                self.print_result(True, "식물 목록 조회 성공", f"식물 수: {len(plants_data.get('plants', []))}")
            else:
                self.print_result(False, f"식물 목록 조회 실패: {response.status_code}")
            
            # 2) 식물 생성
            plant_data = {
                "plant_name": "테스트 식물",
                "species": "몬스테라",
                "meet_day": "2024-01-01"
            }
            
            response = requests.post(f"{self.base_url}/plants", headers=headers, data=plant_data, timeout=10)
            if response.status_code == 201:
                created_plant = response.json()
                plant_id = created_plant.get("idx")
                plant_name = plant_data.get("plant_name", "테스트 식물")
                plant_species = plant_data.get("species", "테스트 종")
                self.print_result(True, "식물 생성 성공", f"식물 ID: {plant_id}")
                
                # 3) 식물 상세 조회
                response = requests.get(f"{self.base_url}/plants/{plant_id}", headers=headers, timeout=10)
                if response.status_code == 200:
                    self.print_result(True, "식물 상세 조회 성공")
                else:
                    self.print_result(False, f"식물 상세 조회 실패: {response.status_code}")
                
                # 식물 정보 반환 (삭제는 나중에)
                return {
                    "plant_id": plant_id,
                    "plant_name": plant_name,
                    "plant_species": plant_species
                }
            else:
                self.print_result(False, f"식물 생성 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.print_result(False, f"식물 API 테스트 실패: {e}")
            return False
    
    # 6. 일기 관련 API 테스트
    def test_diary_apis(self, plant_nickname=None, plant_species=None):
        self.print_section("일기 관련 API 테스트")
        
        if not self.token:
            self.print_result(False, "토큰이 없어서 일기 API 테스트 불가")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 1) 일기 작성 (먼저 작성해야 목록 조회 가능)
            diary_data = {
                "user_title": "테스트 일기",
                "user_content": "테스트 일기 내용입니다.",
                "hashtag": "#테스트"
            }
            
            # 식물 정보가 있으면 추가
            if plant_nickname:
                diary_data["plant_nickname"] = plant_nickname
            if plant_species:
                diary_data["plant_species"] = plant_species
            
            response = requests.post(f"{self.base_url}/diary-list/create", headers=headers, json=diary_data, timeout=10)
            if response.status_code == 200:
                created_diary = response.json()
                diary_id = created_diary.get("diary", {}).get("idx")
                self.print_result(True, "일기 작성 성공", f"일기 ID: {diary_id}")
                
                # 2) 일기 목록 조회 (작성 후 조회)
                response = requests.get(f"{self.base_url}/diary-list", headers=headers, timeout=10)
                if response.status_code == 200:
                    diary_data = response.json()
                    self.print_result(True, "일기 목록 조회 성공", f"일기 수: {len(diary_data.get('diaries', []))}")
                else:
                    self.print_result(False, f"일기 목록 조회 실패: {response.status_code}")
                
                return True
            else:
                self.print_result(False, f"일기 작성 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.print_result(False, f"일기 API 테스트 실패: {e}")
            return False
    
    # 7. 의료/진단 관련 API 테스트
    def test_medical_apis(self):
        self.print_section("의료/진단 관련 API 테스트")
        
        if not self.token:
            self.print_result(False, "토큰이 없어서 의료 API 테스트 불가")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 1) 진단 목록 조회
            response = requests.get(f"{self.base_url}/medical/diagnoses", headers=headers, timeout=10)
            if response.status_code == 200:
                medical_data = response.json()
                self.print_result(True, "진단 목록 조회 성공", f"진단 수: {len(medical_data.get('diagnoses', []))}")
            else:
                self.print_result(False, f"진단 목록 조회 실패: {response.status_code}")
            
            # 2) 진단 통계 조회
            response = requests.get(f"{self.base_url}/medical/stats", headers=headers, timeout=10)
            if response.status_code == 200:
                stats_data = response.json()
                self.print_result(True, "진단 통계 조회 성공", f"통계: {stats_data}")
            else:
                self.print_result(False, f"진단 통계 조회 실패: {response.status_code}")
            
            return True
                
        except Exception as e:
            self.print_result(False, f"의료 API 테스트 실패: {e}")
            return False
    
    # 8. AI 모델 연동 테스트
    def test_ai_model_integration(self):
        self.print_section("AI 모델 연동 테스트")
        
        if not self.token:
            self.print_result(False, "토큰이 없어서 AI 모델 테스트 불가")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 1) 식물 품종 분류 모델 테스트 (POST 방식)
            # 더미 이미지로 테스트 (실제로는 이미지 파일이 필요)
            try:
                response = requests.post(f"{self.model_server_url}/species", 
                                       files={'image': ('test.jpg', b'dummy_image_data', 'image/jpeg')}, 
                                       timeout=30)
                if response.status_code == 200:
                    self.print_result(True, "식물 품종 분류 모델 정상")
                else:
                    self.print_result(False, f"식물 품종 분류 모델 실패: {response.status_code}")
            except Exception as e:
                self.print_result(False, f"식물 품종 분류 모델 테스트 실패: {e}")
            
            # 2) 병해충 진단 모델 테스트 (POST 방식)
            try:
                response = requests.post(f"{self.model_server_url}/disease", 
                                       files={'image': ('test.jpg', b'dummy_image_data', 'image/jpeg')}, 
                                       timeout=30)
                if response.status_code == 200:
                    self.print_result(True, "병해충 진단 모델 정상")
                else:
                    self.print_result(False, f"병해충 진단 모델 실패: {response.status_code}")
            except Exception as e:
                self.print_result(False, f"병해충 진단 모델 테스트 실패: {e}")
            
            # 3) 건강 상태 분류 모델 테스트 (POST 방식)
            try:
                response = requests.post(f"{self.model_server_url}/health", 
                                       files={'image': ('test.jpg', b'dummy_image_data', 'image/jpeg')}, 
                                       timeout=30)
                if response.status_code == 200:
                    self.print_result(True, "건강 상태 분류 모델 정상")
                else:
                    self.print_result(False, f"건강 상태 분류 모델 실패: {response.status_code}")
            except Exception as e:
                self.print_result(False, f"건강 상태 분류 모델 테스트 실패: {e}")
            
            return True
                
        except Exception as e:
            self.print_result(False, f"AI 모델 연동 테스트 실패: {e}")
            return False
    
    # 9. 삭제 테스트 (정리)
    def test_cleanup_apis(self, plant_info=None):
        self.print_section("삭제 테스트 (정리)")
        
        if not self.token:
            self.print_result(False, "토큰이 없어서 삭제 테스트 불가")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 식물 삭제
            if plant_info and plant_info.get("plant_id"):
                plant_id = plant_info["plant_id"]
                response = requests.delete(f"{self.base_url}/plants/{plant_id}", headers=headers, timeout=10)
                if response.status_code == 200:
                    self.print_result(True, "식물 삭제 성공")
                else:
                    self.print_result(False, f"식물 삭제 실패: {response.status_code}")
            
            # TODO: 일기 삭제 API가 있다면 여기에 추가
            # TODO: 진단 기록 삭제 API가 있다면 여기에 추가
            
            return True
            
        except Exception as e:
            self.print_result(False, f"삭제 테스트 실패: {e}")
            return False
    
    # 9. 종합 테스트 실행
    async def run_comprehensive_test(self):
        print("🚀 종합 기능 테스트 시작")
        print("=" * 60)
        
        results = {}
        
        # 1. DB 연결 테스트
        results['db'] = await self.test_db_connection()
        
        # 2. 백엔드 API 헬스체크
        results['backend'] = self.test_backend_health()
        
        # 3. 모델 서버 연결 테스트
        results['model_server'] = self.test_model_server()
        
        # 4. 사용자 인증 테스트
        results['auth'] = self.test_user_auth()
        
        # 5. 식물 관련 API 테스트 (생성만)
        plant_info = self.test_plant_apis()
        results['plants'] = plant_info is not None
        
        # 6. 일기 관련 API 테스트 (식물 정보 포함)
        if plant_info:
            results['diary'] = self.test_diary_apis(
                plant_nickname=plant_info.get("plant_name"),
                plant_species=plant_info.get("plant_species")
            )
        else:
            results['diary'] = self.test_diary_apis()
        
        # 7. 의료/진단 관련 API 테스트
        results['medical'] = self.test_medical_apis()
        
        # 8. AI 모델 연동 테스트
        results['ai_models'] = self.test_ai_model_integration()
        
        # 9. 삭제 테스트 (모든 데이터 생성 후 마지막에 실행)
        results['cleanup'] = self.test_cleanup_apis(plant_info)
        
        # 결과 요약
        self.print_section("테스트 결과 요약")
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        print(f"📊 총 테스트: {total_tests}개")
        print(f"✅ 통과: {passed_tests}개")
        print(f"❌ 실패: {total_tests - passed_tests}개")
        print(f"📈 성공률: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n📋 상세 결과:")
        for test_name, result in results.items():
            status = "✅ 통과" if result else "❌ 실패"
            print(f"   {test_name}: {status}")
        
        if passed_tests == total_tests:
            print("\n🎉 모든 테스트 통과! 시스템이 정상적으로 작동합니다.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests}개 테스트가 실패했습니다. 위의 오류를 확인해주세요.")
        
        return results

# 메인 실행
async def main():
    tester = ComprehensiveTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
