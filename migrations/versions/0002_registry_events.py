"""proxy.registry_events: register/unregister history

Revision ID: 0002
Revises: 0001
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE proxy.registry_events (
            id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            ts         TIMESTAMPTZ NOT NULL,
            network_id TEXT NOT NULL,
            peer_id    TEXT NOT NULL,
            event      TEXT NOT NULL,
            host       TEXT,
            port       INTEGER,
            message    TEXT
        )
    """)
    op.execute("CREATE INDEX ix_registry_events_net_ts ON proxy.registry_events (network_id, ts)")
    op.execute("CREATE INDEX ix_registry_events_peer ON proxy.registry_events (network_id, peer_id, ts)")


def downgrade() -> None:
    op.execute("DROP TABLE proxy.registry_events")
