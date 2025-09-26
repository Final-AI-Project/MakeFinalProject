"""
습도 기반 급수 예측 모델 클라이언트
"""
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from core.config import settings

logger = logging.getLogger(__name__)

class HumidityPredictionClient:
    """습도 예측 모델 서버 클라이언트"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.MODEL_SERVER_URL
        self.timeout = settings.MODEL_SERVER_TIMEOUT
    
    async def predict_watering_time(
        self, 
        current_humidity: float,
        min_humidity: float,
        temperature: float,
        hour_of_day: float,
        s_ref: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        급수 예측을 수행합니다.
        
        Args:
            current_humidity: 현재 습도 (0-100)
            min_humidity: 최소 습도 임계값 (0-100)
            temperature: 현재 기온 (°C)
            hour_of_day: 현재 시간 (0-24)
            s_ref: 상한 센서 퍼센트 (선택사항)
        
        Returns:
            예측 결과 딕셔너리
        """
        try:
            # 요청 데이터 구성
            request_data = {
                "S_now": current_humidity,
                "S_min_user": min_humidity,
                "temp_C": temperature,
                "hour_of_day": hour_of_day
            }
            
            if s_ref is not None:
                request_data["S_ref"] = s_ref
            
            logger.info(f"습도 예측 요청 - URL: {self.base_url}/predict, 데이터: {request_data}")
            
            # 모델 서버에 요청
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/predict",
                    json=request_data
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"급수 예측 성공: {result}")
                return result
                
        except httpx.TimeoutException:
            logger.error("습도 예측 모델 서버 응답 시간 초과")
            raise Exception("모델 서버 응답 시간 초과")
        except httpx.HTTPStatusError as e:
            logger.error(f"습도 예측 모델 서버 HTTP 오류: {e.response.status_code}")
            raise Exception(f"모델 서버 오류: {e.response.status_code}")
        except Exception as e:
            logger.error(f"습도 예측 중 오류 발생: {str(e)}")
            raise Exception(f"급수 예측 실패: {str(e)}")
    
    def calculate_next_watering_date(self, eta_hours: float) -> str:
        """
        예측된 시간을 기반으로 다음 급수 날짜를 계산합니다.
        
        Args:
            eta_hours: 예측된 시간 (시간 단위)
        
        Returns:
            다음 급수 날짜 문자열 (YYYY-MM-DD HH:MM 형식)
        """
        try:
            # 현재 시간에 예측 시간을 더함
            current_time = datetime.now()
            next_watering_time = current_time + timedelta(hours=eta_hours)
            
            # 날짜 형식으로 반환
            return next_watering_time.strftime("%Y-%m-%d %H:%M")
            
        except Exception as e:
            logger.error(f"다음 급수 날짜 계산 중 오류: {str(e)}")
            # 오류 시 기본값 반환 (24시간 후)
            default_time = datetime.now() + timedelta(hours=24)
            return default_time.strftime("%Y-%m-%d %H:%M")

# 전역 클라이언트 인스턴스
humidity_client = HumidityPredictionClient()
