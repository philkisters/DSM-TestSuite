"""core.run_errors: HTTP errors when communicating with Orchestrator/Proxy

Revision ID: 0014
Revises: 0013
"""
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE core.run_errors (
            id          BIGSERIAL PRIMARY KEY,
            run_id      TEXT NOT NULL REFERENCES core.runs(id) ON DELETE CASCADE,
            step_index  INTEGER NOT NULL,
            name        TEXT NOT NULL,
            params      JSONB NOT NULL DEFAULT '{}'::jsonb,
            error_code  INTEGER,
            error_text  TEXT NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE core.run_errors")
