# 공통 Base, 페이지네이션, 타임존 유틸 스키마

from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")

class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # SQLAlchemy ORM ↔ Pydantic

def utcnow() -> datetime:
    # 응답에 넣을 때 기본값으로 활용 가능
    return datetime.now(tz=timezone.utc)


#======커서 기반 페이지네이션 응답======
# 불필요시 삭제
class CursorPage(OrmBase, Generic[T]):
    items: list[T]
    next_cursor: str | None = Field(default=None, description="다음 페이지 커서")
    has_more: bool = False

# 요청 쿼리 파라미터 바인딩용(선택)
class CursorQuery(OrmBase):
    limit: int = Field(20, ge=1, le=100)
    cursor: str | None = None
