"""merge_commands_pipeline_and_mcc_users

Revision ID: merge_001
Revises: 1440e2851238, 986e5b72bde5
Create Date: 2026-04-19 20:36:12.272106

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'merge_001'
down_revision = ('1440e2851238', '986e5b72bde5')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
