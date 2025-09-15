# 모든 모델을 import하여 SQLAlchemy가 관계를 인식할 수 있도록 함
from .user import User
from .diary import Diary
from .humid_info import HumidInfo
from .img_address import ImgAddress
from .pest_wiki import PestWiki
from .plant_wiki import PlantWiki
from .user_plant import UserPlant

__all__ = [
    "User",
    "Diary", 
    "HumidInfo",
    "ImgAddress",
    "PestWiki",
    "PlantWiki",
    "UserPlant",
]