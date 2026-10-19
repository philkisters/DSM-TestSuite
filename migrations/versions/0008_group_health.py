"""core.group_health: health check history of each group's Orchestrator

Revision ID: 0008
Revises: 0007
"""
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE core.group_health (
            id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            group_id   INTEGER NOT NULL REFERENCES core.groups(id) ON DELETE CASCADE,
            state      TEXT NOT NULL CHECK (state IN ('ONLINE', 'NOT_RESPONDING', 'OFFLINE')),
            failures   INTEGER NOT NULL DEFAULT 0,
            timestamp  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_group_health_group_ts ON core.group_health (group_id, timestamp)")


def downgrade() -> None:
    op.execute("DROP TABLE core.group_health")
