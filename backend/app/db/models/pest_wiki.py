from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class PestWiki(Base):
    __tablename__ = "pest_wiki"

    idx: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pest_id: Mapped[int] = mapped_column(nullable=False)
    cause: Mapped[str] = mapped_column(String(100), nullable=False)
    cure: Mapped[str] = mapped_column(Text, nullable=False)
