"""proxy.registry_events.run_id

Revision ID: 0003
Revises: 0002
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE proxy.registry_events ADD COLUMN run_id TEXT")
    op.execute("CREATE INDEX ix_registry_events_run ON proxy.registry_events (run_id) WHERE run_id IS NOT NULL")


def downgrade() -> None:
    op.execute("DROP INDEX proxy.ix_registry_events_run")
    op.execute("ALTER TABLE proxy.registry_events DROP COLUMN run_id")
