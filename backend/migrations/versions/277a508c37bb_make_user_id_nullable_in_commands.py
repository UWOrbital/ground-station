"""make_user_id_nullable_in_commands

Revision ID: 277a508c37bb
Revises: 7a08f61ca7cc
Create Date: 2026-05-31 21:21:38.605793

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '277a508c37bb'
down_revision = '7a08f61ca7cc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("commands", "user_id", nullable=True, schema="transactional")


def downgrade() -> None:
    op.alter_column("commands", "user_id", nullable=False, schema="transactional")
