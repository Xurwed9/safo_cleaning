from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.contact_translation import ContactTranslation


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)

    phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    whatsapp: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    telegram: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    instagram: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    map_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    translations: Mapped[list["ContactTranslation"]] = relationship(
        "ContactTranslation",
        back_populates="contact",
        cascade="all, delete-orphan",
    )