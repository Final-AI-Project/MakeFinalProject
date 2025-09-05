from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.routers import auth as auth_router
from backend.app.routers import plants as plants_router
from backend.app.routers import users as users_router
from .routers.dashboard import router as dashboard_router

settings = get_settings()


# config.py 가 이미 존재한다고 가정
try:
    from .config import get_settings  # type: ignore
except Exception:  # pragma: no cover
    get_settings = None  # fallback

from .routers.dashboard import router as dashboard_router

app = FastAPI(title="Pland API", version="0.1.0")

# CORS (모바일/프론트 개발 편의)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 헬스/버전 
@app.get("/healthz")
def healthz():
    return {"ok": True, "now": datetime.now(timezone.utc).isoformat()}

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


# 라우터 마운트 (/api/v1)
app.include_router(dashboard_router, prefix="/api/v1")

# 서브 앱 문서 활성화 (127.0.0.1:8000/docs에서 서브 앱 api까지 확인할 수 있도록)
api = FastAPI(
    title=f"{settings.APP_NAME} API",
    version=settings.VERSION,
    docs_url="/docs",          # /api/v1/docs
    redoc_url="/redoc",        # /api/v1/redoc
    openapi_url="/openapi.json"
)

api.include_router(auth_router.router)
api.include_router(users_router.router)
api.include_router(plants_router.router)

app.mount(settings.API_V1_PREFIX, api)  # /api/v1