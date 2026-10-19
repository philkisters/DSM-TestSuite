"""proxy.registry_events.peer_data (neighbors, later fingertable / stored images)

Revision ID: 0012
Revises: 0011
"""
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE proxy.registry_events ADD COLUMN peer_data JSONB")


def downgrade() -> None:
    op.execute("ALTER TABLE proxy.registry_events DROP COLUMN peer_data")
