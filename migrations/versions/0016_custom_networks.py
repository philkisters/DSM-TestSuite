"""core.networks for persisted custom network protocol settings

Revision ID: 0016
Revises: 0015
"""
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE core.networks (
            id                    SERIAL PRIMARY KEY,
            group_id              INTEGER NOT NULL REFERENCES core.groups(id) ON DELETE CASCADE,
            network_id            TEXT NOT NULL UNIQUE,
            orchestrator_version  TEXT NOT NULL,
            replication_factor    INTEGER,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_network_orchestrator_version
                CHECK (orchestrator_version IN ('v1', 'v2')),
            CONSTRAINT ck_network_replication
                CHECK (
                    replication_factor IS NULL OR
                    (orchestrator_version = 'v2' AND replication_factor > 0)
                )
        )
    """)
    op.execute("CREATE INDEX ix_networks_group_id ON core.networks (group_id)")


def downgrade() -> None:
    op.execute("DROP TABLE core.networks")
