from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime
from sqlalchemy import Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.db.models.user_plant import UserPlant


class HumidInfo(Base):
    __tablename__ = "humid_info"

    plant_id: Mapped[int] = mapped_column(
        ForeignKey("user_plant.plant_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,   # FK이자 PK로 사용 
        nullable=False,
    )

    humidity: Mapped[float] = mapped_column(Float, nullable=False)
    humid_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 관계 (user_plant 모델과 연결)
    plant: Mapped["UserPlant"] = relationship(back_populates="humid_infos")
