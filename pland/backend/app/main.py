"""
Plant Whisperer FastAPI Application
식물 스피킹 진단 웹앱의 메인 FastAPI 애플리케이션
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.config import settings
from app.routers import health, infer, train, models

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # Startup
    logger.info("Starting Plant Whisperer Backend...")
    
    # Create necessary directories
    import os
    os.makedirs(settings.storage_path, exist_ok=True)
    os.makedirs(settings.model_cache_dir, exist_ok=True)
    os.makedirs(settings.sample_data_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    logger.info("Backend startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Plant Whisperer Backend...")


# Create FastAPI application
app = FastAPI(
    title="Plant Whisperer API",
    description="식물 스피킹 진단 웹앱 API - 식물 사진을 업로드하면 품종과 병충해를 분석하여 자연어로 결과를 전달합니다.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(infer.router, prefix="/api", tags=["inference"])
app.include_router(train.router, prefix="/api", tags=["training"])
app.include_router(models.router, prefix="/api", tags=["models"])

# Mount static files for uploaded images (optional)
app.mount("/uploads", StaticFiles(directory="storage/uploads"), name="uploads")


@app.get("/")
async def root() -> Dict[str, Any]:
    """루트 엔드포인트"""
    return {
        "message": "🌱 Plant Whisperer API에 오신 것을 환영합니다!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 처리"""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 처리"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return {
        "error": "내부 서버 오류가 발생했습니다.",
        "status_code": 500
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.backend_reload,
        log_level=settings.log_level.lower()
    )
