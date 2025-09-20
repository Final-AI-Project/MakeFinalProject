from __future__ import annotations

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from core.config import settings
from db.pool import init_pool, close_pool
from utils.errors import register_error_handlers

# 라우터 임포트
from api import (
    auth_router,
    diary_router,
    diary_list_router,
    info_room_router,
    pest_diagnosis_router,
    plants_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    await init_pool()
    yield
    # 종료 시
    await close_pool()

app = FastAPI(
    title="Pland API", 
    version="0.1.0",
    lifespan=lifespan
)

register_error_handlers(app)

# Static 파일 서빙 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# 라우터 등록
app.include_router(auth_router)
app.include_router(diary_router)
app.include_router(diary_list_router)
app.include_router(info_room_router)
app.include_router(pest_diagnosis_router)
app.include_router(plants_router)

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

@app.get("/health")
def health():
    return {"status": "healthy"}

# DB 헬스체크
@app.get("/health/db")
async def health_db():
    from db.transaction import get_cursor
    async with get_cursor() as cursor:
        await cursor.execute("SELECT 1")
    return {"db": "ok"}

# 버전 정보
@app.get("/version")
def version():
    return {
        "app": "Pland API", 
        "api_v": "0.1.0"
    }
