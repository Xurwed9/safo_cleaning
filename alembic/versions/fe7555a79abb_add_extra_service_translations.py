"""add extra service translations

Revision ID: fe7555a79abb
Revises: ff2f1622996a
Create Date: 2026-10-07 16:05:22.014975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fe7555a79abb'
down_revision: Union[str, Sequence[str], None] = 'ff2f1622996a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
        op.f("ix_extra_service_translations_extra_service_id"),
        "extra_service_translations",
        ["extra_service_id"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_table("extra_service_translations")