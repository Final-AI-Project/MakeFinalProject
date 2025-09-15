from __future__ import annotations

import base64
import json
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from utils.weather_client import WeatherClient
from .users_service import UsersService

# 간단 라우팅/집계 오케스트레이터
@dataclass
class DashboardService:
    weather_client: WeatherClient
    users_service: UsersService

    # -------- Weather --------
    async def get_weather_for_preference(self, prefs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        선호 지역에서 날씨 조회. 실패 시 None 반환(상위에서 null 처리).
        """
        try:
            wl = prefs.get("weather_location") or {}
            code = wl.get("location_code", "SEOUL_KR")
            name = wl.get("name", "Seoul, KR")
            raw = await self.weather_client.get_weather(code)
            # 인터페이스 표준화
            return {
                "location_code": code,
                "name": name,
                "temp_c": float(raw["temp_c"]),
                "condition": raw["condition"],
                "icon_url": raw["icon_url"],
                "updated_at": raw["updated_at"],
            }
        except Exception:
            return None

    # -------- Plants (Stub) --------
    async def list_plants_summary(self, user_id: str, limit: int, cursor: Optional[str]) -> Dict[str, Any]:
        """
        스와이프 카드용 식물 요약 리스트 (커서 기반).
        외부 저장소 연동 전까지 메모리/더미 데이터 사용.
        """
        items_all = _get_or_seed_user_plants(user_id)

        start_idx = 0
        if cursor:
            try:
                start_idx = _decode_cursor(cursor).get("offset", 0)
            except Exception:
                # 커서가 손상되었으면 처음부터
                start_idx = 0

        end_idx = min(start_idx + limit, len(items_all))
        window = items_all[start_idx:end_idx]

        # brief_status 간단 규칙 생성
        now = datetime.now(timezone.utc)
        out_items: List[Dict[str, Any]] = []
        for p in window:
            # 랜덤 규칙 예시
            soil_ok = random.random() > 0.35
            if soil_ok:
                brief = "토양 수분 적정. 24시간 후 재확인 권장."
            else:
                brief = "토양 수분 낮음. 오늘 저녁 100ml 권장."

            last_update = now - timedelta(minutes=random.randint(10, 180))
            out_items.append(
                {
                    "plant_id": p["plant_id"],
                    "nickname": p["nickname"],
                    "brief_status": brief,
                    "last_update_at": last_update,
                    "thumbnail_url": p.get("thumbnail_url"),
                    "detail_path": f"/plants/{p['plant_id']}",
                }
            )

        has_more = end_idx < len(items_all)
        next_cursor = _encode_cursor({"offset": end_idx}) if has_more else None

        return {
            "items": out_items,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }

# -----------------------
# In-memory stub storage
# -----------------------
_USER_PLANTS_DB: Dict[str, List[Dict[str, Any]]] = {}

def _get_or_seed_user_plants(user_id: str) -> List[Dict[str, Any]]:
    if user_id in _USER_PLANTS_DB:
        return _USER_PLANTS_DB[user_id]

    # 샘플 시드 (실제 구현 시 DB 연동)
    nicknames = [
        "초코몬스테라", "룰루필로덴드론", "레모니카스", "무화과베이비",
        "피톤치드소나무", "카랑코에", "금사철", "칼라디움",
        "헬로마리모", "행운목", "올리브", "스킨답서스"
    ]
    seeded: List[Dict[str, Any]] = []
    for i, n in enumerate(nicknames, 1):
        plant_id = str(uuid.uuid4())
        thumb = None
        if i % 3 == 0:
            thumb = f"https://picsum.photos/seed/{plant_id[:8]}/256/256"
        seeded.append(
            {"plant_id": plant_id, "nickname": n, "thumbnail_url": thumb}
        )

    _USER_PLANTS_DB[user_id] = seeded
    return seeded

# -----------------------
# Opaque cursor helpers
# -----------------------
def _encode_cursor(obj: Dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(obj).encode("utf-8")).decode("utf-8")

def _decode_cursor(s: str) -> Dict[str, Any]:
    pad = '=' * ((4 - len(s) % 4) % 4)
    raw = base64.urlsafe_b64decode((s + pad).encode("utf-8")).decode("utf-8")
    return json.loads(raw)
