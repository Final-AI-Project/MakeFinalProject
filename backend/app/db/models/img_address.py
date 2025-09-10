from __future__ import annotations

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

from backend.app.db.models.diary import Diary


class ImgAddress(Base):
    __tablename__ = "img_address"

    idx: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    diary_id: Mapped[int] = mapped_column(
        ForeignKey("diary.diary_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )

    img_url: Mapped[str | None] = mapped_column(String(300))

    # 관계 (Diary 모델과 연결)
    diary: Mapped["Diary"] = relationship(back_populates="images")
