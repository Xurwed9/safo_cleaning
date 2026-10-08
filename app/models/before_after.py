from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.before_after_translation import BeforeAfterTranslation


class BeforeAfter(Base):
    __tablename__ = "before_after"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    before_image: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    after_image: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    translations: Mapped[
        list["BeforeAfterTranslation"]
    ] = relationship(
        "BeforeAfterTranslation",
        back_populates="before_after",
        cascade="all, delete-orphan",
        lazy="selectin",
    )