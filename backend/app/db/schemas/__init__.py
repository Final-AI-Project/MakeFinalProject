# app/schemas/__init__.py
from .common import CursorPage, CursorQuery, OrmBase

from .user import UserCreate, UserUpdate, UserOut
from .diary import DiaryCreate, DiaryUpdate, DiaryOut
from .img_address import ImgAddressCreate, ImgAddressOut
from .user_plant import UserPlantCreate, UserPlantUpdate, UserPlantOut
from .humid_info import HumidInfoCreate, HumidInfoOut
from .plant_wiki import PlantWikiCreate, PlantWikiUpdate, PlantWikiOut
from .pest_wiki import PestWikiCreate, PestWikiUpdate, PestWikiOut

# 추가한 스키마들을 모두 import하고 __all__에 포함시킴
__all__ = [
    "OrmBase", "CursorPage", "CursorQuery",
    "UserCreate", "UserUpdate", "UserOut",
    "DiaryCreate", "DiaryUpdate", "DiaryOut",
    "ImgAddressCreate", "ImgAddressOut",
    "UserPlantCreate", "UserPlantUpdate", "UserPlantOut",
    "HumidInfoCreate", "HumidInfoOut",
    "PlantWikiCreate", "PlantWikiUpdate", "PlantWikiOut",
    "PestWikiCreate", "PestWikiUpdate", "PestWikiOut",
]

