"""add admin request status to mcc users

Revision ID: db826cddfa25
Revises: 5ca1f847cae4
Create Date: 2026-08-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'db826cddfa25'
down_revision = '5ca1f847cae4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    admin_request_status_enum = sa.Enum(
        'NOT_REQUESTED', 'PENDING', 'APPROVED', 'REJECTED', name='mccadminrequeststatus'
    )
    admin_request_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'users_data',
        sa.Column(
            'admin_request_status',
            admin_request_status_enum,
            nullable=False,
            server_default='NOT_REQUESTED',
        ),
        schema='mcc_users',
    )


def downgrade() -> None:
    op.drop_column('users_data', 'admin_request_status', schema='mcc_users')
    op.execute('DROP TYPE IF EXISTS mccadminrequeststatus')
