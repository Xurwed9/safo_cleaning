"""restore extra service translations

Revision ID: dfe8ed933a5d
Revises: 9ce227b27eee
Create Date: 2026-10-07 17:33:37.031477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfe8ed933a5d'
down_revision: Union[str, Sequence[str], None] = '9ce227b27eee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Restore extra_service_translations table."""

    op.create_table(
        "extra_service_translations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("extra_service_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["extra_service_id"],
            ["extra_services.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "extra_service_id",
            "language",
            name="uq_extra_service_translation_language",
        ),
    )

    op.create_index(
        "ix_extra_service_translations_extra_service_id",
        "extra_service_translations",
        ["extra_service_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove extra_service_translations table."""

    op.drop_index(
        "ix_extra_service_translations_extra_service_id",
        table_name="extra_service_translations",
    )

    op.drop_table("extra_service_translations")