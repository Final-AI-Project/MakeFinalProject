# 더미 날씨 클라이언트
from typing import Dict, Any

class WeatherClient:
    """더미 날씨 클라이언트 - 실제 날씨 API 연동 시 교체 필요"""
    
    async def get_weather(self, location: str) -> Dict[str, Any]:
        """더미 날씨 정보 반환"""
        return {
            "condition": "맑음",
            "temperature": 22,
            "humidity": 60,
            "icon_url": "https://example.com/sunny.png"
        }
