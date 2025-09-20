"""
라우터 통합 진입점
"""
from fastapi import APIRouter
from routers.plants import router as home_router
from routers.diary_list import router as diary_list_router
from routers.info_room import router as info_room_router
from routers.auth import router as auth_router
from routers.plants import router as plants_router
from routers.diary import router as diary_router
from routers.medical import router as medical_router
from routers.disease_diagnosis import router as disease_diagnosis_router
from routers import detail_router, diary_router as plant_diary_router, pest_router, watering_router, images_router
from routers.diary import router as diary_write_router
from routers.pest_diagnosis import router as pest_diagnosis_router

router = APIRouter()

# 페이지 라우터 등록
router.include_router(home_router)  # /home
router.include_router(diary_list_router)  # /diary-list
router.include_router(info_room_router)  # /info-room

# 기능 라우터 등록
router.include_router(auth_router)  # /auth
router.include_router(plants_router)  # /plants
router.include_router(diary_router)  # /diary
router.include_router(medical_router)  # /medical
router.include_router(disease_diagnosis_router)  # /disease-diagnosis
router.include_router(detail_router)  # /plant-detail
router.include_router(plant_diary_router)  # /plant-detail/{plant_idx}/diaries
router.include_router(pest_router)  # /plant-detail/{plant_idx}/pest-records
router.include_router(watering_router)  # /plant-detail/{plant_idx}/watering-records
router.include_router(images_router)  # /plant-detail/{plant_idx}/upload-image
router.include_router(diary_write_router)  # /diary
router.include_router(pest_diagnosis_router)  # /pest-diagnosis
