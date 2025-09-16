from __future__ import annotations
from pydantic import Field
from .common import OrmBase

class PestWikiCreate(OrmBase):
    pest_id: int
    cause: str | None = None
    cure: str | None = None

class PestWikiUpdate(OrmBase):
    pest_id: int | None = None
    cause: str | None = None
    cure: str | None = None

class PestWikiOut(OrmBase):
    idx: int
    pest_id: int
    cause: str | None
    cure: str | None
