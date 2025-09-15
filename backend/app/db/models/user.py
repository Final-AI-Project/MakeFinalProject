from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.database import Base

if TYPE_CHECKING:
    from ..models.diary import Diary
    from ..models.user_plant import UserPlant


class User(Base):
    __tablename__ = "users"

    idx: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    user_pw: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hp: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(20), nullable=False)
    regdate: Mapped[datetime | None] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # 관계 설정 (Diary 모델과 연결: 1:N)
    diaries: Mapped[list["Diary"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    # 관계 설정 (UserPlant 모델과 연결: 1:N)
    plants: Mapped[list["UserPlant"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
