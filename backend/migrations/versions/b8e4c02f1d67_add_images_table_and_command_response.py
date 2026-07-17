"""add images table and command response

Adds the transactional.images table holding image data downlinked from the OBC,
and a nullable response column on transactional.commands for the OBC's reply.

Revision ID: b8e4c02f1d67
Revises: 551e1cea7b28
Create Date: 2026-07-16 00:00:00.000000

"""

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "b8e4c02f1d67"
down_revision = "551e1cea7b28"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the images table and the commands.response column."""
    op.add_column(
        "commands",
        sa.Column("response", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        schema="transactional",
    )
    op.create_table(
        "images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("data", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("packet_id", sa.Uuid(), nullable=True),
        sa.Column("aro_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["packet_id"], ["transactional.packets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["aro_id"], ["transactional.aro_requests.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="transactional",
    )
    op.create_index(op.f("ix_transactional_images_id"), "images", ["id"], unique=False, schema="transactional")


def downgrade() -> None:
    """Drop the images table and the commands.response column."""
    op.drop_index(op.f("ix_transactional_images_id"), table_name="images", schema="transactional")
    op.drop_table("images", schema="transactional")
    op.drop_column("commands", "response", schema="transactional")
