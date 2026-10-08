from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.contact import Contact


class ContactTranslation(Base):
    __tablename__ = "contact_translations"

    id: Mapped[int] = mapped_column(primary_key=True)

    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    working_hours: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    contact: Mapped["Contact"] = relationship(
        "Contact",
        back_populates="translations",
    )

    __table_args__ = (
        UniqueConstraint(
            "contact_id",
            "language",
            name="uq_contact_translation_language",
        ),
    )