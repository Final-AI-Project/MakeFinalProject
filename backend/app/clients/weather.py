# 프론트엔드에서 받은 날씨 데이터 처리 클라이언트
from typing import Dict, Any

class WeatherClient:
    """프론트엔드에서 받은 날씨 데이터를 처리하는 클라이언트"""
    
    def __init__(self):
        pass
    
    async def get_current_weather(self) -> Dict[str, Any]:
        """
        프론트엔드에서 날씨 데이터를 받지 못한 경우에만 사용하는 기본 날씨 정보
        
        Returns:
            Dict[str, Any]: 기본 날씨 정보
        """
        return self._get_default_weather()
    
    def _get_default_weather(self) -> Dict[str, Any]:
        """프론트엔드에서 날씨 데이터를 받지 못한 경우의 기본 날씨 정보"""
        return {
            "condition": "맑음",
            "temp": 22,  # temperature 대신 temp로 변경
            "humidity": 60,
            "icon_url": "https://openweathermap.org/img/wn/01d@2x.png",
            "description": "clear sky",
            "feels_like": 22,
            "pressure": 1013,
            "wind_speed": 2.5
        }

# 전역 클라이언트 인스턴스
weather_client = WeatherClient()
