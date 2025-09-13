from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from .humid_info import HumidInfo
    from .user import User


class UserPlant(Base):
    __tablename__ = "user_plant"

    idx: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )

    plant_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    plant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    species: Mapped[str | None] = mapped_column(String(100))
    pest_id: Mapped[int | None] = mapped_column(Integer)
    meet_day: Mapped[datetime | None] = mapped_column(DateTime)

    # 관계 설정
    user: Mapped["User"] = relationship(back_populates="plants")
    humid_infos: Mapped[list["HumidInfo"]] = relationship(
        back_populates="plant", cascade="all, delete-orphan"
    )
