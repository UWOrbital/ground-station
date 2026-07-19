"""add_aro_user_keys_table

Revision ID: 380a0576264a
Revises: c7f2a91b4d3e
Create Date: 2026-07-18 22:24:59.143133

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '380a0576264a'
down_revision = 'c7f2a91b4d3e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the aro_user_keys table in the aro_users schema."""
    op.create_table(
        "aro_user_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("key_data", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("synced_to_obc_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["aro_users.users_data.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="aro_users",
    )
    op.create_index(op.f("ix_aro_users_aro_user_keys_id"), "aro_user_keys", ["id"], unique=False, schema="aro_users")


def downgrade() -> None:
    """Drop the aro_user_keys table."""
    op.drop_index(op.f("ix_aro_users_aro_user_keys_id"), table_name="aro_user_keys", schema="aro_users")
    op.drop_table("aro_user_keys", schema="aro_users")
