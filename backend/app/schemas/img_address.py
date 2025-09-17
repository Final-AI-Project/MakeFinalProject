from __future__ import annotations
from pydantic import Field
from .common import OrmBase

class ImgAddressCreate(OrmBase):
    diary_id: int
    img_url: str = Field(min_length=1)

class ImgAddressOut(OrmBase):
    idx: int
    diary_id: int
    img_url: str
