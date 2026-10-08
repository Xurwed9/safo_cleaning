from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.extra_service_translation import (
        ExtraServiceTranslation,
    )
    from app.models.lead_extra_service import LeadExtraService


class ExtraService(Base):
    __tablename__ = "extra_services"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    pricing_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="fixed",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    leads: Mapped[list["LeadExtraService"]] = relationship(
        "LeadExtraService",
        back_populates="extra_service",
    )

    translations: Mapped[
        list["ExtraServiceTranslation"]
    ] = relationship(
        "ExtraServiceTranslation",
        back_populates="extra_service",
        cascade="all, delete-orphan",
        lazy="selectin",
    )