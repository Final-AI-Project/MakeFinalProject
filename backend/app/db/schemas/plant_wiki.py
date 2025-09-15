from __future__ import annotations

from pydantic import Field
from .common import OrmBase

class PlantWikiCreate(OrmBase):
    species: str = Field(min_length=1, max_length=100)
    wiki_img: str = Field(min_length=1, max_length=300)
    sunlight: str | None = Field(default=None, max_length=10)
    watering: int | None = None
    flowering: str | None = Field(default=None, max_length=100)
    fertilizer: str | None = Field(default=None, max_length=100)
    toxic: str | None = Field(default=None, max_length=100)

class PlantWikiUpdate(OrmBase):
    wiki_img: str | None = None
    sunlight: str | None = None
    watering: int | None = None
    flowering: str | None = None
    fertilizer: str | None = None
    toxic: str | None = None

class PlantWikiOut(OrmBase):
    idx: int
    species: str
    wiki_img: str
    sunlight: str | None
    watering: int | None
    flowering: str | None
    fertilizer: str | None
    toxic: str | None
