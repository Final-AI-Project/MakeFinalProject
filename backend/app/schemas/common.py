from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class OrmBase(BaseModel):
    """SQLAlchemy ORM ↔ Pydantic 변환용 베이스"""
    model_config = ConfigDict(from_attributes=True)  # SQLAlchemy ORM ↔ Pydantic


class CursorPage(BaseModel):
    """커서 기반 페이지네이션 응답"""
    items: list[Any]
    next_cursor: Optional[str] = None
    has_more: bool = False


class CursorQuery(BaseModel):
    """커서 기반 페이지네이션 쿼리 파라미터"""
    limit: int = 10
    cursor: Optional[str] = None
