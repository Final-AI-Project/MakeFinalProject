from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from backend.app.db.models.user import User
from backend.app.db.models.img_address import ImgAddress

class Diary(Base):
    __tablename__ = "diary"
    
    diary_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        index=True,
        nullable=False,
    )

    user_title: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str | None] = mapped_column(String(300))
    user_content: Mapped[str | None] = mapped_column(Text)
    hashtag: Mapped[str | None] = mapped_column(String(1000))
    plant_content: Mapped[str | None] = mapped_column(Text)
    weather: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = relationship(back_populates="diaries")
    images: Mapped[list["ImgAddress"]] = relationship(
        back_populates="diary", cascade="all, delete-orphan"
    )
    