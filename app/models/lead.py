from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.lead_note import LeadNote
    from app.models.lead_extra_service import LeadExtraService
    from app.models.notification import Notification
    from app.models.analytics_event import AnalyticsEvent


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)

    object_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    area: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    cleaning_frequency: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="ru",
    )

    calculated_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    consent_given: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    consent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="new",
        index=True,
    )

    assigned_manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    assigned_manager: Mapped["User | None"] = relationship(
        "User",
        back_populates="assigned_leads",
        foreign_keys=[assigned_manager_id],
    )

    notes: Mapped[list["LeadNote"]] = relationship(
        "LeadNote",
        back_populates="lead",
        cascade="all, delete-orphan",
    )

    extra_services: Mapped[list["LeadExtraService"]] = relationship(
        "LeadExtraService",
        back_populates="lead",
        cascade="all, delete-orphan",
    )

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="lead",
        cascade="all, delete-orphan",
    )
    analytics_events: Mapped[list["AnalyticsEvent"]] = relationship(
    "AnalyticsEvent",
    back_populates="lead",
    )

    __table_args__ = (
        Index("ix_leads_created_at", "created_at"),
        Index("ix_leads_status_created_at", "status", "created_at"),
    )