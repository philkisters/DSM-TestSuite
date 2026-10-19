"""baseline: proxy.events and core tables

Revision ID: 0001
Revises:
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS proxy")
    op.execute("CREATE SCHEMA IF NOT EXISTS core")

    op.execute("""
        CREATE TABLE proxy.events (
            id         BIGINT GENERATED ALWAYS AS IDENTITY,
            ts         TIMESTAMPTZ NOT NULL,
            run_id     TEXT,
            network_id TEXT NOT NULL,
            src_peer   TEXT,
            dst_peer   TEXT,
            code       SMALLINT,
            size       INTEGER NOT NULL DEFAULT 0,
            corr_id    TEXT,
            status     TEXT NOT NULL,
            delay_ms   REAL,
            content    JSONB,
            PRIMARY KEY (id, ts)
        ) PARTITION BY RANGE (ts)
    """)
    op.execute("CREATE TABLE proxy.events_default PARTITION OF proxy.events DEFAULT")
    op.execute("CREATE INDEX ix_events_net_ts ON proxy.events (network_id, ts)")
    op.execute("CREATE INDEX ix_events_net_code ON proxy.events (network_id, code)")
    op.execute("CREATE INDEX ix_events_run ON proxy.events (run_id) WHERE run_id IS NOT NULL")

    op.execute("""
        CREATE TABLE core.groups (
            id         SERIAL PRIMARY KEY,
            network_id TEXT NOT NULL UNIQUE,
            name       TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE core.challenges (
            id          SERIAL PRIMARY KEY,
            key         TEXT NOT NULL UNIQUE,
            title       TEXT NOT NULL,
            phase       TEXT NOT NULL,
            description TEXT
        )
    """)
    op.execute("""
        CREATE TABLE core.runs (
            id           TEXT PRIMARY KEY,
            group_id     INTEGER NOT NULL REFERENCES core.groups(id),
            challenge_id INTEGER NOT NULL REFERENCES core.challenges(id),
            seed         BIGINT,
            status       TEXT NOT NULL,
            started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at  TIMESTAMPTZ,
            metrics      JSONB
        )
    """)
    op.execute("""
        CREATE TABLE core.achievements (
            id    SERIAL PRIMARY KEY,
            key   TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL
        )
    """)
    op.execute("""
        CREATE TABLE core.group_achievements (
            group_id       INTEGER NOT NULL REFERENCES core.groups(id),
            achievement_id INTEGER NOT NULL REFERENCES core.achievements(id),
            earned_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (group_id, achievement_id)
        )
    """)


def downgrade() -> None:
    op.execute("DROP SCHEMA core CASCADE")
    op.execute("DROP SCHEMA proxy CASCADE")
