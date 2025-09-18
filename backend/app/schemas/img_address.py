from __future__ import annotations
from pydantic import Field
from .common import OrmBase

class ImgAddressCreate(OrmBase):
    diary_id: int
    img_url: str = Field(min_length=1)
    status: int | None = None  # 1: 품종분류용/식물 프로필 이미지, 2: 일기 이미지, 3: 기타

class ImgAddressOut(OrmBase):
    idx: int
    diary_id: int
    img_url: str
    status: int | None
