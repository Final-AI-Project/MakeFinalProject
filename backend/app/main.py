from __future__ import annotations

import os
from datetime import datetime, timezone
from sqlalchemy import text

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.database import engine

try:
    from .core.config import get_settings  # type: ignore
except Exception:  # pragma: no cover
    get_settings = None  # fallback

# 서브 앱 라우터 임포트 (테스트 편의용)
from backend.app.routers.dashboard import router as dashboard_router
from backend.app.routers.auth import router as auth_router
from backend.app.routers.plants import router as plants_router
from backend.app.routers.images import router as images_router

from backend.app.utils.errors import register_error_handlers

import backend.app.db.models 


app = FastAPI(title="Pland API", version="0.1.0")

register_error_handlers(app) # 에러 핸들러 등록

# 라우터 등록 (확인용)
app.include_router(images_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1") 
app.include_router(auth_router, prefix="/api/v1")
app.include_router(plants_router, prefix="/api/v1")

# CORS (모바일/프론트 개발 편의)
app.add_middleware(
    CORSMiddleware,
    # 프론트엔드 주소 허용 (임시)
    allow_origins=["http://localhost:8080", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 헬스체크
@app.get("/healthcheck")
def healthcheck():
    return {"ok": True, "now": datetime.now(timezone.utc).isoformat()}

# DB 헬스체크
@app.get("/health/db")
async def health_db():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
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