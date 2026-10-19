"""core.run_assertions: result of every assertion step of a run

Revision ID: 0007
Revises: 0006
"""
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE core.run_assertions (
            id          BIGSERIAL PRIMARY KEY,
            run_id      TEXT NOT NULL REFERENCES core.runs(id) ON DELETE CASCADE,
            step_index  INTEGER NOT NULL,
            name        TEXT NOT NULL,
            params      JSONB NOT NULL DEFAULT '{}'::jsonb,
            passed      BOOLEAN NOT NULL,
            message     TEXT,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (run_id, step_index)
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE core.run_assertions")
