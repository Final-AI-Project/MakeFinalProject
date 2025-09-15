from __future__ import annotations

from pydantic import Field
from .common import OrmBase

class PestWikiCreate(OrmBase):
    pest_id: int
    cause: str = Field(min_length=1, max_length=100)
    cure: str

class PestWikiUpdate(OrmBase):
    cause: str | None = None
    cure: str | None = None

class PestWikiOut(OrmBase):
    idx: int
    pest_id: int
    cause: str
    cure: str
