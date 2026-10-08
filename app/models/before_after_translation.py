from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.before_after import BeforeAfter


class BeforeAfterTranslation(Base):
    __tablename__ = "before_after_translations"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    before_after_id: Mapped[int] = mapped_column(
        ForeignKey(
            "before_after.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    before_after: Mapped["BeforeAfter"] = relationship(
        "BeforeAfter",
        back_populates="translations",
    )

    __table_args__ = (
        UniqueConstraint(
            "before_after_id",
            "language",
            name="uq_before_after_translation_language",
        ),
    )