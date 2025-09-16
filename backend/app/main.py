from __future__ import annotations

import os
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import get_db_connection

try:
    from core.config import get_settings  # type: ignore
except Exception:  # pragma: no cover
    get_settings = None  # fallback


# 서브 앱 라우터 임포트
from routers.dashboard import router as dashboard_router
from routers.auth import router as auth_router
from routers.plants import router as plants_router
from routers.images import router as images_router
from routers.ai import router as ai_router
from utils.errors import register_error_handlers

# import db.models  # 임시 주석처리 


app = FastAPI(title="Pland API", version="0.1.0")

register_error_handlers(app) # 에러 핸들러 등록

# 라우터 등록 (확인용)
app.include_router(images_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1") 
app.include_router(auth_router)  # auth는 prefix 없이 직접 등록
app.include_router(plants_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")  # AI 기능 라우터

# CORS (모바일/프론트 개발 편의) - 모든 오리진 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용 (개발용)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 헬스체크
@app.get("/healthcheck")
def healthcheck():
    return {"ok": True, "now": datetime.now(timezone.utc).isoformat()}


# DB 헬스체크
@app.get("/health/db")
async def health_db():
    async with get_db_connection() as (conn, cursor):
        await cursor.execute("SELECT 1")
    return {"db": "ok"}

# 버전 정보
@app.get("/version")
def version():
    if get_settings:
        try:
            s = get_settings()
            return {
                "app": getattr(s, "APP_NAME", "Pland API"),
                "api_v": getattr(s, "VERSION", "0.1.0"),
            }
        except Exception:
            pass
    return {"app": "Pland API", "api_v": "0.1.0"}


# uvicorn backend.app.main:app --reload