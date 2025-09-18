# app/providers/weather_provider.py
from typing import List, Dict
import csv
from ..config import settings
from ..schemas import WeatherPoint

def to_epoch_ms(ts_sec: int) -> int:
    return int(ts_sec * 1000)

class WeatherProvider:
    async def get_forecast(self, lat: float, lon: float, hours: int) -> List[WeatherPoint]:
        raise NotImplementedError

class FakeWeatherProvider(WeatherProvider):
    async def get_forecast(self, lat: float, lon: float, hours: int) -> List[WeatherPoint]:
        # 개발용: CSV를 그대로 읽어 WeatherPoint로 반환
        out: List[WeatherPoint] = []
        with open(settings.fake_forecast_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= hours:
                    break
                out.append(WeatherPoint(
                    ts=int(row["ts"]),
                    outdoor_temp_c=float(row["outdoor_temp_c"]),
                    outdoor_rh_pct=float(row["outdoor_rh_pct"]),
                    irradiance_wpm2=float(row.get("irradiance_wpm2", 0) or 0),
                ))
        return out

class KMAWeatherProvider(WeatherProvider):
    async def get_forecast(self, lat: float, lon: float, hours: int) -> List[WeatherPoint]:
        # TODO: 1) 위경도→격자 변환(DFS)
        #       2) 초단기/단기 예보 API 호출 (온도/습도/일사·대체변수)
        #       3) 발표시각/적용시각 정렬
        #       4) WeatherPoint 리스트로 변환
        # 여기서는 스텁으로 FAKE를 재사용(로컬 테스트 가능)
        fake = FakeWeatherProvider()
        return await fake.get_forecast(lat, lon, hours)

def get_weather_provider() -> WeatherProvider:
    if settings.weather_provider.upper() == "FAKE":
        return FakeWeatherProvider()
    return KMAWeatherProvider()
