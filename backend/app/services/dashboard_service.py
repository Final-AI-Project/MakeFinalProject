from __future__ import annotations

import base64
import json
import random
import uuid
import aiomysql

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from utils.weather_client import WeatherClient
from .users_service import UsersService


# 커서 헬퍼
def _encode_cursor(obj: Dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(obj).encode("utf-8")).decode("utf-8")

def _decode_cursor(s: str) -> Dict[str, Any]:
    pad = '=' * ((4 - len(s) % 4) % 4)
    raw = base64.urlsafe_b64decode((s + pad).encode("utf-8")).decode("utf-8")
    return json.loads(raw)

@dataclass
class DashboardService:
    """
    DB 기반 대시보드 서비스
    - 프론트가 넘겨준 날씨를 가볍게 검증, 정규화 (브릿지)
    - user_plant, humid_info로 "내 식물" 카드 목록 구성 (커서 기반 페이징)
    """
    conn: aiomysql.Connection
    cursor: aiomysql.DictCursor

    # weather bridge
    async def normalize_weather_from_front(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        프론트에서 받은 날씨 정보를 서버 표준 포맷으로 정규화
        - 검증: 필수 필드 존재 여부
        - 정규화: 타입 변환, 기본값 설정
        - 서버 타임스탬프 추가
        """
        # 필수 필드 검증
        required_fields = ["location_code", "name", "temp_c"]
        for field in required_fields:
            if field not in raw:
                raise ValueError(f"Missing required field: {field}")

        # 타입 변환 및 기본값 설정
        normalized = {
            "location_code": str(raw["location_code"]),
            "name": str(raw["name"]),
            "temp_c": float(raw["temp_c"]),
            "condition": str(raw.get("condition", "")),
            "icon_url": str(raw.get("icon_url", "")),
            "updated_at": raw.get("updated_at"),
            "server_received_at": datetime.now(timezone.utc).isoformat(),
        }
        
        return normalized
    
    # plants summary 
    async def list_plants_summary(
            self,
            *,
            user_id: str,
            limit: int,
            cursor: Optional[str],
    ) -> Dict[str, Any]:
        """
        스와이프 카드용 식물 요약 리스트
        - 정렬: user_plant.idx DESC
        - 커서: 마지막 idx 기준으로 그 다음 페이지
        - humid_info: 각 plant_id별 최신 1건 조인
        """
        last_idx: Optional[int] = None
        if cursor:
            try:
                last_idx = int(_decode_cursor(cursor).get("last_idx", 0)) or None
            except Exception:
                last_idx = None

        # 1) 내 식물 목록 조회 (limit+1 로 has_more 판정)
        if last_idx is not None:
            query = """
                SELECT * FROM user_plant 
                WHERE user_id = %s AND idx < %s 
                ORDER BY idx DESC 
                LIMIT %s
            """
            params = (user_id, last_idx, limit + 1)
        else:
            query = """
                SELECT * FROM user_plant 
                WHERE user_id = %s 
                ORDER BY idx DESC 
                LIMIT %s
            """
            params = (user_id, limit + 1)
        
        await self.cursor.execute(query, params)
        ups = await self.cursor.fetchall()
        has_more = len(ups) > limit
        ups = ups[:limit]

        if not ups:
            return {"items": [], "next_cursor": None, "has_more": False}

        # 2) 해당 plant_id 목록
        plant_ids = [u['plant_id'] for u in ups]

        # 3) 각 plant_id별 최신 습도 정보 조회
        humid_map = {}
        if plant_ids:
            placeholders = ','.join(['%s'] * len(plant_ids))
            humid_query = f"""
                SELECT h.* FROM humid_info h
                INNER JOIN (
                    SELECT plant_id, MAX(humid_date) as max_date
                    FROM humid_info 
                    WHERE plant_id IN ({placeholders})
                    GROUP BY plant_id
                ) latest ON h.plant_id = latest.plant_id AND h.humid_date = latest.max_date
            """
            await self.cursor.execute(humid_query, plant_ids)
            humids = await self.cursor.fetchall()
            humid_map = {h['plant_id']: h for h in humids}

        # 4) 응답 구성
        items = []
        for up in ups:
            plant_id = up['plant_id']
            humid_info = humid_map.get(plant_id)
            
            # 해충 상태 판정 (pest_id가 있으면 해충 있음)
            pest_status = "has_pest" if up.get('pest_id') else "healthy"
            
            item = {
                "plant_id": plant_id,
                "plant_name": up['plant_name'],
                "species": up.get('species'),
                "pest_status": pest_status,
                "pest_id": up.get('pest_id'),
                "humidity": humid_info['humidity'] if humid_info else None,
                "humid_date": humid_info['humid_date'].isoformat() if humid_info and humid_info['humid_date'] else None,
                "detail_path": f"/plants/{plant_id}",
            }
            items.append(item)

        # 5) 다음 커서 생성
        next_cursor = None
        if has_more and items:
            last_item_idx = ups[-1]['idx']
            next_cursor = _encode_cursor({"last_idx": last_item_idx})

        return {
            "items": items,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }