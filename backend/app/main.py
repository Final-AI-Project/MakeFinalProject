from __future__ import annotations

import os
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from core.config import get_settings  # type: ignore
except Exception:  # pragma: no cover
    get_settings = None  # fallback

# 서브 앱 라우터 임포트
from routers.dashboard import router as dashboard_router
from routers.auth import router as auth_router
from routers.plants import router as plants_router
from routers.images import router as images_router

from utils.errors import register_error_handlers


app = FastAPI(title="Pland API", version="0.1.0")
# app = FastAPI()


register_error_handlers(app) # 에러 핸들러 등록

# 라우터 등록 (확인용)
app.include_router(images_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1") 
app.include_router(auth_router)  # auth는 prefix 없이 직접 등록
app.include_router(plants_router, prefix="/api/v1")

# CORS (모바일/프론트 개발 편의) - 모든 오리진 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용 (개발용)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 정적 파일 서빙 (개발용)
# media_dir = (settings.ROOT_DIR / settings.MEDIA_ROOT)
# media_dir.mkdir(parents=True, exist_ok=True)  # 없으면 생성
# app.mount(settings.MEDIA_URL, StaticFiles(directory=media_dir), name="media")


# 기존 헬스/버전 (유지)
@app.get("/healthcheck")
def healthcheck():
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




# uvicorn backend.app.main:app --reload
