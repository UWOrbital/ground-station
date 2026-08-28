"""add aro request delete_deadline

Adds the nullable transactional.aro_requests.delete_deadline column holding the
time until which a PENDING picture request may still be deleted by its ARO.

Revision ID: f3a9c1d24b70
Revises: 5ca1f847cae4
Create Date: 2026-08-26 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f3a9c1d24b70"
down_revision = "5ca1f847cae4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the aro_requests.delete_deadline column."""
    op.add_column(
        "aro_requests",
        sa.Column("delete_deadline", sa.DateTime(timezone=True), nullable=True),
        schema="transactional",
    )


def downgrade() -> None:
    """Drop the aro_requests.delete_deadline column."""
    op.drop_column("aro_requests", "delete_deadline", schema="transactional")
