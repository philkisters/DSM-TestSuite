"""drop run_id from proxy.events and proxy.registry_events (network_id is unique per core.runs)

Revision ID: 0006
Revises: 0005
"""
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS proxy.ix_events_run")
    op.execute("ALTER TABLE proxy.events DROP COLUMN run_id")
    op.execute("DROP INDEX IF EXISTS proxy.ix_registry_events_run")
    op.execute("ALTER TABLE proxy.registry_events DROP COLUMN run_id")


def downgrade() -> None:
    op.execute("ALTER TABLE proxy.registry_events ADD COLUMN run_id TEXT")
    op.execute("CREATE INDEX ix_registry_events_run ON proxy.registry_events (run_id) WHERE run_id IS NOT NULL")
    op.execute("ALTER TABLE proxy.events ADD COLUMN run_id TEXT")
    op.execute("CREATE INDEX ix_events_run ON proxy.events (run_id) WHERE run_id IS NOT NULL")
