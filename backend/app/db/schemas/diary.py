from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel

# 일단 연결만!! 추후 필요 시 확장/변경

class DiarySchema(BaseModel):
    diary_id: int
    user_id: str
    user_title: str
    img_url: str | None
    user_content: str | None
    hashtag: str | None
    plant_content: str | None
    weather: str | None
    created_at: datetime | None

    # ORM 모드 활성화
    class Config:
        orm_mode = True
