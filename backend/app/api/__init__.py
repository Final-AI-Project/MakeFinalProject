"""
라우터 모듈 통합 진입점
"""
from .detail import router as detail_router
from .diary import router as diary_router
from .pest import router as pest_router
from .watering import router as watering_router
from .images import router as images_router

__all__ = [
    "detail_router",
    "diary_router", 
    "pest_router",
    "watering_router",
    "images_router"
]