from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.extra_service import ExtraService


class ExtraServiceTranslation(Base):
    __tablename__ = "extra_service_translations"

    id: Mapped[int] = mapped_column(primary_key=True)

    extra_service_id: Mapped[int] = mapped_column(
        ForeignKey(
            "extra_services.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    extra_service: Mapped["ExtraService"] = relationship(
        "ExtraService",
        back_populates="translations",
    )

    extra_service: Mapped["ExtraService"] = relationship(
    "ExtraService",
    back_populates="translations",
    )

    __table_args__ = (
        UniqueConstraint(
            "extra_service_id",
            "language",
            name="uq_extra_service_translation_language",
        ),
    )
