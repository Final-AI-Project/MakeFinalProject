from __future__ import annotations

from pydantic import BaseModel
from .common import OrmBase

class ImgAddressCreate(OrmBase):
    diary_id: int
    img_url: str | None = None  # 파일 저장 후 서비스에서 채움

class ImgAddressOut(OrmBase):
    idx: int
    diary_id: int
    img_url: str | None
