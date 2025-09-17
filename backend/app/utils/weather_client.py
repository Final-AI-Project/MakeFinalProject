from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Dict

# 외부 API 교체를 고려한 인터페이스 스텁
class WeatherClient:
    """
    향후 실제 외부 API로 교체될 수 있도록 인터페이스만 고정.
    현재는 더미 값(난수/고정 조합) 반환.
    """

    CONDITIONS = [
        ("Sunny", "https://cdn-icons-png.flaticon.com/512/869/869869.png"),
        ("Cloudy", "https://cdn-icons-png.flaticon.com/512/414/414825.png"),
        ("Rain", "https://cdn-icons-png.flaticon.com/512/1163/1163624.png"),
        ("Partly Cloudy", "https://cdn-icons-png.flaticon.com/512/252/252035.png"),
    ]

    async def get_weather(self, location_code: str) -> Dict:
        # 간단 난수 기반 스텁 (지역 코드에 따른 온도 가중치 예시)
        base = 23.0
        if location_code.upper().startswith("SEOUL"):
            base = 24.0
        elif location_code.upper().endswith("_KR"):
            base = 23.5

        temp = round(base + random.uniform(-3.0, 3.0), 1)
        condition, icon = random.choice(self.CONDITIONS)

        return {
            "temp_c": temp,
            "condition": condition,
            "icon_url": icon,
            "updated_at": datetime.now(timezone.utc),
        }
