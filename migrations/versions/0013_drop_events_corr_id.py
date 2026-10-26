"""drop unused corr_id from proxy.events

Revision ID: 0013
Revises: 0012
"""
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE proxy.events DROP COLUMN corr_id")


def downgrade() -> None:
    op.execute("ALTER TABLE proxy.events ADD COLUMN corr_id TEXT")
