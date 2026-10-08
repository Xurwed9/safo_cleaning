from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.lead import Lead
    from app.models.extra_service import ExtraService


class LeadExtraService(Base):
    __tablename__ = "lead_extra_services"

    id: Mapped[int] = mapped_column(primary_key=True)

    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    extra_service_id: Mapped[int] = mapped_column(
        ForeignKey("extra_services.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    price_at_submission: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    lead: Mapped["Lead"] = relationship(
        "Lead",
        back_populates="extra_services",
    )

    extra_service: Mapped["ExtraService"] = relationship(
        "ExtraService",
        back_populates="leads",
    )
    __table_args__ = (
        UniqueConstraint(
            "lead_id",
            "extra_service_id",
            name="uq_lead_extra_service",
        )
    ),