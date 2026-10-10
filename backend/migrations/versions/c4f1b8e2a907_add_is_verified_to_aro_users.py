"""add is_verified to aro users

Revision ID: c4f1b8e2a907
Revises: db826cddfa25
Create Date: 2026-09-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c4f1b8e2a907'
down_revision = 'db826cddfa25'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users_data',
        sa.Column(
            'is_verified',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        schema='aro_users',
    )


def downgrade() -> None:
    op.drop_column('users_data', 'is_verified', schema='aro_users')
