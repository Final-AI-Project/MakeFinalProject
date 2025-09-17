from __future__ import annotations
from typing import List
from pydantic import Field
from .common import OrmBase

class PlantWikiCreate(OrmBase):
    species: str = Field(min_length=1, max_length=100)
    wiki_image: str | None = None
    sunlight: str | None = None
    watering: str | None = None
    flowering: str | None = None
    fertilizer: str | None = None
    toxicity: str | None = None

class PlantWikiUpdate(OrmBase):
    species: str | None = None
    wiki_image: str | None = None
    sunlight: str | None = None
    watering: str | None = None
    flowering: str | None = None
    fertilizer: str | None = None
    toxicity: str | None = None

class PlantWikiOut(OrmBase):
    idx: int
    species: str
    wiki_image: str | None
    sunlight: str | None
    watering: str | None
    flowering: str | None
    fertilizer: str | None
    toxicity: str | None

class PlantWikiListOut(OrmBase):
    items: List[PlantWikiOut]
    next_cursor: str | None
    has_more: bool