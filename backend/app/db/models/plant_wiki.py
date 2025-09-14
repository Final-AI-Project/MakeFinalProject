from __future__ import annotations

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
# db 수정 반영 아직 안됨

class PlantWiki(Base):
    __tablename__ = "plant_wiki"

    idx: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    species: Mapped[str] = mapped_column(String(100), nullable=False)
    wiki_img: Mapped[str] = mapped_column(String(300), nullable=False)

    sunlight: Mapped[str | None] = mapped_column(String(10))
    watering: Mapped[int | None] = mapped_column(Integer)
    flowering: Mapped[str | None] = mapped_column(String(100))
    fertilizer: Mapped[str | None] = mapped_column(String(100))
    toxic: Mapped[str | None] = mapped_column(String(100))
