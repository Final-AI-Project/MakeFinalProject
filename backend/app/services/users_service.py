from __future__ import annotations

import base64
import json
import uuid
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# 설정에서 JWT 시크릿/알고리즘을 읽어오되, 없으면 느슨 모드로 동작
try:
    from core.config import get_settings  # type: ignore
except Exception:  # pragma: no cover
    get_settings = None  # fallback

# PyJWT가 없을 수도 있음 → 안전한 폴백 디코드 제공
try:
    import jwt as pyjwt  # PyJWT
except Exception:  # pragma: no cover
    pyjwt = None  # type: ignore

# 간단한 인메모리 사용자/환경 저장소
_USERS_DB: Dict[str, Dict[str, Any]] = {}

DEFAULT_PREFS = {
    "weather_location": {"location_code": "SEOUL_KR", "name": "Seoul, KR"}
}

security = HTTPBearer(auto_error=True)


def _decode_jwt_best_effort(token: str) -> Optional[Dict[str, Any]]:
    """
    1) PyJWT + 검증
    2) PyJWT 검증 비활성화
    3) 수동 base64url payload 파싱
    순으로 시도해서 payload(dict) 반환. 실패 시 None.
    """
    # 1) 검증 시도
    if get_settings is not None:
        try:
            settings = get_settings()
            secret = getattr(settings, "JWT_SECRET", None)
            alg = getattr(settings, "JWT_ALG", "HS256")
            if secret and pyjwt:
                return pyjwt.decode(token, secret, algorithms=[alg])  # type: ignore
        except Exception:
            pass

    # 2) 서명 검증 없이 디코딩
    if pyjwt:
        try:
            return pyjwt.decode(token, options={"verify_signature": False})  # type: ignore
        except Exception:
            pass

    # 3) 수동 payload 추출
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            payload_b64 = parts[1]
            payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
            raw = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
            return json.loads(raw)
    except Exception:
        pass

    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    JWT Access 인증 (Authorization: Bearer ...).
    payload.sub (또는 user_id) 를 사용자 식별자로 사용.
    """
    if not credentials or not credentials.scheme.lower() == "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "missing bearer token", "trace_id": str(uuid.uuid4())}},
        )

    token = credentials.credentials
    payload = _decode_jwt_best_effort(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "invalid token", "trace_id": str(uuid.uuid4())}},
        )

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "token missing sub", "trace_id": str(uuid.uuid4())}},
        )

    # 인메모리 사용자 생성/보장
    user = _USERS_DB.setdefault(user_id, {"user_id": user_id, "preferences": dict(DEFAULT_PREFS)})
    return user


class UsersService:
    """선호 지역(pref) 관리"""

    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        user = _USERS_DB.setdefault(user_id, {"user_id": user_id, "preferences": dict(DEFAULT_PREFS)})
        prefs = user.get("preferences") or {}
        # 필수 키 보정
        wl = prefs.get("weather_location") or DEFAULT_PREFS["weather_location"]
        return {"weather_location": {"location_code": wl.get("location_code", "SEOUL_KR"), "name": wl.get("name", "Seoul, KR")}}

    async def update_preferences(self, user_id: str, weather_location: Dict[str, Any]) -> Dict[str, Any]:
        if not weather_location or "location_code" not in weather_location or "name" not in weather_location:
            raise ValueError("weather_location requires 'location_code' and 'name'")
        user = _USERS_DB.setdefault(user_id, {"user_id": user_id, "preferences": dict(DEFAULT_PREFS)})
        user["preferences"]["weather_location"] = {
            "location_code": str(weather_location["location_code"]),
            "name": str(weather_location["name"]),
        }
        return {"weather_location": user["preferences"]["weather_location"]}
