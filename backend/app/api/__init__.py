"""
API 라우터 모듈 통합 진입점
"""
from .auth import router as auth_router
from .diary import router as diary_router
from .diary_list import router as diary_list_router
from .info_room import router as info_room_router
from .pest_diagnosis import router as pest_diagnosis_router
from .plants import router as plants_router

__all__ = [
    "auth_router",
    "diary_router",
    "diary_list_router", 
    "info_room_router",
    "pest_diagnosis_router",
    "plants_router"
]