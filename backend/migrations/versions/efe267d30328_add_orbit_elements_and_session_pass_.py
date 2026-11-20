"""add orbit elements and session pass fields

Revision ID: efe267d30328
Revises: c4f1b8e2a907
Create Date: 2026-11-18 23:46:56.042101

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'efe267d30328'
down_revision = 'c4f1b8e2a907'
branch_labels = None
depends_on = None

SCHEMA = 'transactional'

CHECK_CONSTRAINTS = (
    ('ck_sessions_start_before_end', 'start_time < end_time'),
    (
        'ck_sessions_predicted_fields',
        "source <> 'PREDICTED' OR (rise_time IS NOT NULL AND peak_time IS NOT NULL AND set_time IS NOT NULL"
        " AND min_elevation_deg IS NOT NULL AND max_elevation_deg IS NOT NULL AND rise_azimuth_deg IS NOT NULL"
        " AND set_azimuth_deg IS NOT NULL AND orbit_element_id IS NOT NULL)",
    ),
    ('ck_sessions_pass_order', 'rise_time < peak_time AND peak_time < set_time'),
    ('ck_sessions_padding_outside_pass', 'start_time <= rise_time AND set_time <= end_time'),
    ('ck_sessions_min_elevation_range', 'min_elevation_deg >= 0 AND min_elevation_deg <= 90'),
    ('ck_sessions_max_elevation_range', 'max_elevation_deg >= 0 AND max_elevation_deg <= 90'),
    ('ck_sessions_peak_above_cutoff', 'max_elevation_deg > min_elevation_deg'),
    (
        'ck_sessions_azimuth_range',
        'rise_azimuth_deg >= 0 AND rise_azimuth_deg < 360 AND set_azimuth_deg >= 0 AND set_azimuth_deg < 360',
    ),
)


def upgrade() -> None:
    # add_column doesn't create enum types (create_table does), so create sessionsource explicitly
    sa.Enum('PREDICTED', 'MANUAL', name='sessionsource').create(op.get_bind(), checkfirst=True)

    op.create_table('orbit_elements',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('norad_cat_id', sa.Integer(), nullable=False),
    sa.Column('epoch', sa.DateTime(timezone=True), nullable=False),
    sa.Column('omm', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('source', sa.Enum('CELESTRAK', 'MANUAL', name='orbitelementsource'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('norad_cat_id', 'epoch', name='uq_orbit_elements_norad_cat_id_epoch'),
    schema=SCHEMA
    )

    # Existing sessions become manual sessions
    op.add_column('sessions', sa.Column('source', sa.Enum('PREDICTED', 'MANUAL', name='sessionsource'), nullable=False, server_default='MANUAL'), schema=SCHEMA)
    op.add_column('sessions', sa.Column('rise_time', sa.DateTime(timezone=True), nullable=True), schema=SCHEMA)
    op.add_column('sessions', sa.Column('peak_time', sa.DateTime(timezone=True), nullable=True), schema=SCHEMA)
    op.add_column('sessions', sa.Column('set_time', sa.DateTime(timezone=True), nullable=True), schema=SCHEMA)
    op.add_column('sessions', sa.Column('min_elevation_deg', sa.Float(), nullable=True), schema=SCHEMA)
    op.add_column('sessions', sa.Column('max_elevation_deg', sa.Float(), nullable=True), schema=SCHEMA)
    op.add_column('sessions', sa.Column('rise_azimuth_deg', sa.Float(), nullable=True), schema=SCHEMA)
    op.add_column('sessions', sa.Column('set_azimuth_deg', sa.Float(), nullable=True), schema=SCHEMA)
    op.add_column('sessions', sa.Column('orbit_element_id', sa.Uuid(), nullable=True), schema=SCHEMA)
    op.add_column('sessions', sa.Column('orphaned_at', sa.DateTime(timezone=True), nullable=True), schema=SCHEMA)
    op.create_index(op.f('ix_transactional_sessions_end_time'), 'sessions', ['end_time'], unique=False, schema=SCHEMA)
    op.create_index(op.f('ix_transactional_sessions_start_time'), 'sessions', ['start_time'], unique=False, schema=SCHEMA)
    op.create_foreign_key('sessions_orbit_element_id_fkey', 'sessions', 'orbit_elements', ['orbit_element_id'], ['id'], source_schema=SCHEMA, referent_schema=SCHEMA, ondelete='RESTRICT')

    # Autogenerate doesn't detect check constraints; keep these in sync with Session.__table_args__
    for name, condition in CHECK_CONSTRAINTS:
        op.create_check_constraint(name, 'sessions', condition, schema=SCHEMA)


def downgrade() -> None:
    for name, _ in reversed(CHECK_CONSTRAINTS):
        op.drop_constraint(name, 'sessions', schema=SCHEMA, type_='check')

    op.drop_constraint('sessions_orbit_element_id_fkey', 'sessions', schema=SCHEMA, type_='foreignkey')
    op.drop_index(op.f('ix_transactional_sessions_start_time'), table_name='sessions', schema=SCHEMA)
    op.drop_index(op.f('ix_transactional_sessions_end_time'), table_name='sessions', schema=SCHEMA)
    op.drop_column('sessions', 'orphaned_at', schema=SCHEMA)
    op.drop_column('sessions', 'orbit_element_id', schema=SCHEMA)
    op.drop_column('sessions', 'set_azimuth_deg', schema=SCHEMA)
    op.drop_column('sessions', 'rise_azimuth_deg', schema=SCHEMA)
    op.drop_column('sessions', 'max_elevation_deg', schema=SCHEMA)
    op.drop_column('sessions', 'min_elevation_deg', schema=SCHEMA)
    op.drop_column('sessions', 'set_time', schema=SCHEMA)
    op.drop_column('sessions', 'peak_time', schema=SCHEMA)
    op.drop_column('sessions', 'rise_time', schema=SCHEMA)
    op.drop_column('sessions', 'source', schema=SCHEMA)
    op.drop_table('orbit_elements', schema=SCHEMA)

    # drop_table/drop_column don't drop enum types
    op.execute('DROP TYPE IF EXISTS sessionsource')
    op.execute('DROP TYPE IF EXISTS orbitelementsource')
