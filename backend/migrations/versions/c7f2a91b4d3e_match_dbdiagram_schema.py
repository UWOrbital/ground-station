"""match dbdiagram schema

Restructures the transactional schema to link commands/telemetry directly to
packets (dropping the packet_commands / packet_telemetry join tables), renames
comms_session -> sessions and packet -> packets, updates the command/aro status
enums, and renames the ARO auth columns (user_data_id -> user_id,
auth_type -> type, token -> uuid).

Revision ID: c7f2a91b4d3e
Revises: 277a508c37bb
Create Date: 2026-06-03 00:00:00.000000

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7f2a91b4d3e"
down_revision = "277a508c37bb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the schema changes that bring the database in line with the dbdiagram design."""
    # --- Drop the aro_requests -> packet_commands FK so the join tables can be removed ---
    op.drop_constraint("aro_requests_packet_id_fkey", "aro_requests", schema="transactional", type_="foreignkey")

    # --- Drop the join tables (commands/telemetry now reference packets directly) ---
    op.drop_index(op.f("ix_transactional_packet_telemetry_id"), table_name="packet_telemetry", schema="transactional")
    op.drop_table("packet_telemetry", schema="transactional")
    op.drop_index(op.f("ix_transactional_packet_commands_id"), table_name="packet_commands", schema="transactional")
    op.drop_table("packet_commands", schema="transactional")

    # --- Rename comms_session -> sessions ---
    op.rename_table("comms_session", "sessions", schema="transactional")
    op.execute("ALTER INDEX transactional.ix_transactional_comms_session_id RENAME TO ix_transactional_sessions_id")

    # --- Rename packet -> packets ---
    op.rename_table("packet", "packets", schema="transactional")
    op.execute("ALTER INDEX transactional.ix_transactional_packet_id RENAME TO ix_transactional_packets_id")

    # --- packets: new subtype column ---
    op.add_column(
        "packets",
        sa.Column("subtype", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        schema="transactional",
    )

    # --- aro_requests: repoint packet_id FK onto packets ---
    op.create_foreign_key(
        "aro_requests_packet_id_fkey",
        "aro_requests",
        "packets",
        ["packet_id"],
        ["id"],
        source_schema="transactional",
        referent_schema="transactional",
        ondelete="CASCADE",
    )

    # --- commandstatus enum: drop SENT/PACKETED, add ONGOING (Postgres can't drop enum values in place) ---
    op.execute("ALTER TYPE commandstatus RENAME TO commandstatus_old")
    op.execute(
        "CREATE TYPE commandstatus AS ENUM "
        "('PENDING', 'SCHEDULED', 'ONGOING', 'CANCELLED', 'FAILED', 'COMPLETED')"
    )
    op.execute(
        "ALTER TABLE transactional.commands ALTER COLUMN status TYPE commandstatus "
        "USING (CASE WHEN status::text IN ('SENT', 'PACKETED') THEN 'ONGOING' ELSE status::text END)::commandstatus"
    )
    op.execute("DROP TYPE commandstatus_old")

    # --- commands: direct link to a packet ---
    op.add_column("commands", sa.Column("packet_id", sa.Uuid(), nullable=True), schema="transactional")
    op.add_column("commands", sa.Column("sequence_index", sa.Integer(), nullable=True), schema="transactional")
    op.create_foreign_key(
        "commands_packet_id_fkey",
        "commands",
        "packets",
        ["packet_id"],
        ["id"],
        source_schema="transactional",
        referent_schema="transactional",
        ondelete="SET NULL",
    )

    # --- telemetry: direct link to a packet plus a capture timestamp ---
    op.add_column("telemetry", sa.Column("packet_id", sa.Uuid(), nullable=True), schema="transactional")
    op.add_column("telemetry", sa.Column("sequence_index", sa.Integer(), nullable=True), schema="transactional")
    op.add_column(
        "telemetry",
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        schema="transactional",
    )
    op.create_foreign_key(
        "telemetry_packet_id_fkey",
        "telemetry",
        "packets",
        ["packet_id"],
        ["id"],
        source_schema="transactional",
        referent_schema="transactional",
        ondelete="SET NULL",
    )

    # --- arorequeststatus enum: ONGOING -> TAKEN ---
    op.execute("ALTER TYPE arorequeststatus RENAME VALUE 'ONGOING' TO 'TAKEN'")

    # --- ARO auth column renames ---
    op.alter_column("user_login", "user_data_id", new_column_name="user_id", schema="aro_users")
    op.alter_column("auth_tokens", "user_data_id", new_column_name="user_id", schema="aro_users")
    op.alter_column("auth_tokens", "auth_type", new_column_name="type", schema="aro_users")
    op.execute("ALTER TABLE aro_users.auth_tokens ALTER COLUMN token TYPE uuid USING token::uuid")


def downgrade() -> None:
    """Revert the dbdiagram schema changes."""
    # --- ARO auth column renames ---
    op.execute("ALTER TABLE aro_users.auth_tokens ALTER COLUMN token TYPE varchar USING token::text")
    op.alter_column("auth_tokens", "type", new_column_name="auth_type", schema="aro_users")
    op.alter_column("auth_tokens", "user_id", new_column_name="user_data_id", schema="aro_users")
    op.alter_column("user_login", "user_id", new_column_name="user_data_id", schema="aro_users")

    # --- arorequeststatus enum: TAKEN -> ONGOING ---
    op.execute("ALTER TYPE arorequeststatus RENAME VALUE 'TAKEN' TO 'ONGOING'")

    # --- telemetry: drop direct packet link ---
    op.drop_constraint("telemetry_packet_id_fkey", "telemetry", schema="transactional", type_="foreignkey")
    op.drop_column("telemetry", "timestamp", schema="transactional")
    op.drop_column("telemetry", "sequence_index", schema="transactional")
    op.drop_column("telemetry", "packet_id", schema="transactional")

    # --- commands: drop direct packet link ---
    op.drop_constraint("commands_packet_id_fkey", "commands", schema="transactional", type_="foreignkey")
    op.drop_column("commands", "sequence_index", schema="transactional")
    op.drop_column("commands", "packet_id", schema="transactional")

    # --- commandstatus enum: restore SENT/PACKETED, drop ONGOING ---
    op.execute("ALTER TYPE commandstatus RENAME TO commandstatus_old")
    op.execute(
        "CREATE TYPE commandstatus AS ENUM "
        "('PENDING', 'SCHEDULED', 'SENT', 'CANCELLED', 'FAILED', 'COMPLETED', 'PACKETED')"
    )
    op.execute(
        "ALTER TABLE transactional.commands ALTER COLUMN status TYPE commandstatus "
        "USING (CASE WHEN status::text = 'ONGOING' THEN 'SENT' ELSE status::text END)::commandstatus"
    )
    op.execute("DROP TYPE commandstatus_old")

    # --- aro_requests: repoint packet_id FK back onto packet_commands ---
    op.drop_constraint("aro_requests_packet_id_fkey", "aro_requests", schema="transactional", type_="foreignkey")

    # --- packets: drop subtype ---
    op.drop_column("packets", "subtype", schema="transactional")

    # --- Rename packets -> packet ---
    op.execute("ALTER INDEX transactional.ix_transactional_packets_id RENAME TO ix_transactional_packet_id")
    op.rename_table("packets", "packet", schema="transactional")

    # --- Rename sessions -> comms_session ---
    op.execute("ALTER INDEX transactional.ix_transactional_sessions_id RENAME TO ix_transactional_comms_session_id")
    op.rename_table("sessions", "comms_session", schema="transactional")

    # --- Recreate the join tables ---
    op.create_table(
        "packet_commands",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("packet_id", sa.Uuid(), nullable=False),
        sa.Column("command_id", sa.Uuid(), nullable=False),
        sa.Column("previous", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["command_id"], ["transactional.commands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["packet_id"], ["transactional.packet.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["previous"], ["transactional.commands.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="transactional",
    )
    op.create_index(
        op.f("ix_transactional_packet_commands_id"), "packet_commands", ["id"], unique=False, schema="transactional"
    )
    op.create_table(
        "packet_telemetry",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("packet_id", sa.Uuid(), nullable=False),
        sa.Column("telemetry_id", sa.Uuid(), nullable=False),
        sa.Column("previous", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["packet_id"], ["transactional.packet.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["previous"], ["transactional.telemetry.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["telemetry_id"], ["transactional.telemetry.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="transactional",
    )
    op.create_index(
        op.f("ix_transactional_packet_telemetry_id"), "packet_telemetry", ["id"], unique=False, schema="transactional"
    )

    op.create_foreign_key(
        "aro_requests_packet_id_fkey",
        "aro_requests",
        "packet_commands",
        ["packet_id"],
        ["id"],
        source_schema="transactional",
        referent_schema="transactional",
        ondelete="CASCADE",
    )
